import hashlib
import urllib
from urllib.parse import ParseResult, urlparse
from urllib.robotparser import RobotFileParser

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from common.constants import USER_AGENT
from database.database_manager import DatabaseManager
from database.models import Page, PageData
from logger.logger import logger
from services.link_extractor import find_links
from services.page_extractor import (
    find_sitemap_links,
    get_page,
    find_images,
    extract_binary_links,
)
from util.util import fix_shortened_url, get_site_ip, canonicalize, block_aggressively


async def crawl_url(
    start_url: str,
    browser_page: Page,
    robot_file_parser: RobotFileParser,
    database_manager: DatabaseManager,
    page_id: int,
):
    """
    Crawls the provided current_url.
    :param start_url: Url to be crawled
    :param browser_page: Browser page
    :param robot_file_parser: parser for robots.txt
    :param database_manager: manager for database calls
    :param page_id: If of the current page
    :return:
    """
    logger.info(f"Crawling url {start_url} started.")

    # Fix shortened URLs (if necessary).
    current_url = fix_shortened_url(url=start_url)

    # Parse url into a ParseResult object.
    current_url_parsed: ParseResult = urlparse(current_url)

    # Get url domain
    domain = current_url_parsed.netloc

    # Get site's ip address
    ip = get_site_ip(hostname=domain)

    # If the DNS request failed it probably doesn't work.
    if ip is None:
        logger.info(f"DNS request failed for url {current_url}.")
        return

    # Get saved site from the database (if exists)
    saved_site = await database_manager.get_site(domain=domain)

    site_id: int
    if saved_site:
        # Don't request sitemaps if the domain was already visited
        sitemap_urls = set()
        logger.debug(
            f"Domain {domain} was already visited so sitemaps will be ignored."
        )
        site_id, domain, robots_content, sitemap_content = saved_site
    else:
        logger.debug(f"Domain {domain} has not been visited yet.")

        sitemap_content = None
        if robot_file_parser.site_maps() is not None:
            sitemap_content = ",".join(robot_file_parser.site_maps())
        site_id = await database_manager.save_site(
            domain=domain,
            sitemap_content=sitemap_content,
            robots_content=robot_file_parser.__str__(),
        )

        sitemap_urls = await find_sitemap_links(
            current_url=current_url_parsed,
            robot_file_parser=robot_file_parser,
            domain=domain,
            ip=ip,
        )

    page_urls = set()
    # Fetch page
    try:
        (url, html, data_type, status, accessed_time) = await get_page(
            url=current_url,
            page=browser_page,
            domain=domain,
            ip=ip,
            robot_delay=robot_file_parser.crawl_delay(useragent=USER_AGENT),
        )
        # Convert actual page url to canonical form
        page_url = "".join(canonicalize({url}))
        # Check if URL is a redirect by matching current_url and returned url and the reassigning Only checking HTTP
        # response status for direct is most likely not enough since there could be a redirect with JS
        if current_url != page_url:
            # Page saves happen later in the execution, the important thing is the set the proper context (i.e. the url)
            # for all the following operations
            logger.debug(
                f"Current watched url {current_url} differs from actual browser url {page_url}. Redirect happened."
            )

            # Save original page as a redirect
            await database_manager.update_page_redirect(
                page_id=page_id, site_id=site_id, accessed_time=accessed_time
            )

            # Create new page to act as the current one
            new_page_id = await database_manager.create_new_page(
                url=page_url, site_id=site_id
            )

            # link previous page to the new redirected page.
            await database_manager.add_page_link(
                to_page_id=new_page_id, from_page_id=page_id
            )
            page_id = new_page_id
            logger.info(f"Url {current_url} redirected to {page_url}.")

        else:
            logger.debug(
                f"Current watched url matches the actual browser url (i.e. no redirects happened)."
            )

        if html:
            # Generate html hash
            html_hash = hashlib.sha256(html.encode("utf-8")).hexdigest()

            # Check whether the html hash matches any other hash in the database.
            page_collision = await database_manager.check_pages_hash_collision(
                html_hash=html_hash
            )
            if page_collision is not None:
                original_page_id, original_site_id = page_collision
                await database_manager.update_page(
                    page_id=page_id,
                    status=status,
                    site_id=original_site_id,
                    page_type_code="DUPLICATE",
                    accessed_time=accessed_time,
                )
                # link duplicate page to the original one.
                await database_manager.add_page_link(
                    to_page_id=original_page_id, from_page_id=page_id
                )
                logger.info(f"Url {current_url} is a duplicate of another page.")

            else:
                # PARSE PAGE
                # extract any relevant data from the page here, using BeautifulSoup
                beautiful_soup = BeautifulSoup(html, "html.parser")

                # get images
                page_images = find_images(beautiful_soup)

                # get URLs
                page_urls = find_links(
                    beautiful_soup,
                    current_url_parsed,
                    robot_file_parser=robot_file_parser,
                )

                # check page URLs for binary file link and place them in separate list
                (page_urls, page_data_entries) = extract_binary_links(urls=page_urls)

                # SAVE PAGE
                # Save page to the database
                await database_manager.update_page(
                    page_id=page_id,
                    html=html,
                    status=status,
                    site_id=site_id,
                    html_hash=html_hash,
                    accessed_time=accessed_time,
                )

                # SAVE PAGE IMAGES
                for image in page_images:
                    image.page_id = page_id
                if len(page_images) > 0:
                    await database_manager.save_images(images=list(page_images))

                # SAVE PAGE DATA
                for page_data in page_data_entries:
                    page_data.page_id = page_id
                if len(page_data_entries) > 0:
                    await database_manager.save_page_data(
                        page_data_entries=list(page_data_entries)
                    )
        else:
            logger.debug(
                f"Page {current_url} html is empty, this hopefully means that the page returned a binary file."
            )

            # SAVE PAGE
            # Check page content type for binary file
            if data_type is not None:
                # Save page as binary
                await database_manager.update_page(
                    site_id=site_id,
                    page_id=page_id,
                    status=status,
                    page_type_code="BINARY",
                    accessed_time=accessed_time,
                )
                # Save page data
                await database_manager.save_page_data(
                    page_data_entries=[
                        PageData(page_id=page_id, data_type_code=data_type)
                    ]
                )
                logger.debug(f"Url {current_url} leads to a binary file {data_type}.")

    except Exception as e:
        # Mark page as failed
        await database_manager.mark_page_as_failed(page_id=page_id, site_id=site_id)

        match str(e).split(" at ")[0]:
            case "net::ERR_BAD_SSL_CLIENT_AUTH_CERT":
                logger.debug(f"Opening page {current_url} failed with an error {e}.")
            case "net::ERR_CONNECTION_RESET":
                logger.debug(f"Opening page {current_url} failed with an error {e}.")
            case "net::ERR_ABORTED":
                logger.debug(f"Opening page {current_url} failed with an error {e}.")
            case "net::ERR_EMPTY_RESPONSE":
                logger.debug(f"Opening page {current_url} failed with an error {e}.")
            case _:
                logger.warning(f"Opening page {current_url} failed with an error {e}.")

    # SAVE PAGE LINKS
    # combine DOM and sitemap URLs
    new_links = page_urls.union(sitemap_urls)
    logger.debug(f"Got {len(new_links)} new links.")
    # Add new urls to the frontier
    for link in new_links:
        link_id = await database_manager.add_to_frontier(link=link)
        if link_id is not None:
            # link previous page to the new link page.
            await database_manager.add_page_link(
                to_page_id=link_id, from_page_id=page_id
            )

    logger.info(f"Crawling url {start_url} finished.")


async def start_spider(database_manager: DatabaseManager):
    """
    Setups the playwright library and starts the crawler.
    """
    logger.info("Spider started.")
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            args=[
                "--ignore-certificate-errors",
                "--ignore-urlfetcher-cert-requests",
                "--ignore-certificate-errors",
                "--allow-running-insecure-content",
                "--ignore-certificate-errors-spki-lis",
            ]
        )

        # browser = await playwright.firefox.launch(firefox_user_prefs={"security.enterprise_roots.enabled": True,
        # "acceptInsecureCerts": True, "security.ssl.enable_ocsp_stapling": False,
        # "network.stricttransportsecurity.preloadlist": False})

        # create a new incognito browser context.
        context = await browser.new_context(
            ignore_https_errors=True,
            user_agent=USER_AGENT,
        )
        # create a new page in a pristine context.
        browser_page = await context.new_page()
        # Prevent loading some resources for better performance.
        await browser_page.route("**/*", block_aggressively)
        robot_file_parser = urllib.robotparser.RobotFileParser()

        frontier_page = await database_manager.pop_frontier()
        while frontier_page is not None:
            frontier_id, url = frontier_page
            try:
                await crawl_url(
                    start_url=url,
                    browser_page=browser_page,
                    robot_file_parser=robot_file_parser,
                    database_manager=database_manager,
                    page_id=frontier_id,
                )
            except Exception as e:
                logger.critical(f"Crawling url {url} failed with an error {e}.")
                await database_manager.mark_page_as_failed(page_id=frontier_id)
            # logger.info(f'Visited {await database_manager.get_html_pages_count()} unique HTML pages.')
            # logger.info(f'Frontier contains {len(await database_manager.get_frontier_links())} unique links.')
            frontier_page = await database_manager.pop_frontier()
    await browser.close()
    logger.info(f"Spider finished.")
