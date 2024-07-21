import os
from datetime import datetime
from mimetypes import guess_extension
from urllib.parse import ParseResult
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from playwright.async_api import Page

from common.constants import PAGE_WAIT_TIMEOUT, image_extensions, USER_AGENT
from database.models import Image, DataType, PageData
from logger.logger import logger
from services.delay_manager import refresh_site_available_time
from services.docoument_extractor import extension_to_datatype
from util.util import canonicalize, is_url_allowed, is_domain_allowed, check_if_binary


async def get_page(
    url: str, page: Page, domain: str, ip: str, robot_delay: str
) -> (str, str, DataType, int):
    """
    Requests and downloads a specific webpage.
    :param url: Webpage url to be crawled.
    :param page: Browser page.
    :return: html, status
    """
    # Wait required delay time
    await refresh_site_available_time(domain=domain, ip=ip, robot_delay=robot_delay)
    accessed_time = datetime.now()
    logger.debug(f"Opening page {url}.")
    try:
        response = await page.goto(url=url, timeout=PAGE_WAIT_TIMEOUT)
        status = response.status
        html = await page.content()
        logger.debug(f"Response status is {status}.")
        return page.url, html, None, status, accessed_time
    except Exception as e:
        match str(e).split(" at ")[0]:
            case "net::ERR_ABORTED":
                # Maybe the file is of a binary type, try 2 download it.
                logger.debug(f"Going to the page failed, initiating download mode.")
                try:
                    # Wait required delay time
                    await refresh_site_available_time(
                        domain=domain, ip=ip, robot_delay=robot_delay
                    )
                    document = requests.get(
                        url, verify=False, timeout=PAGE_WAIT_TIMEOUT
                    )
                    accessed_time = datetime.now()
                    status = document.status_code
                    if status != 200:
                        raise Exception(f"Status code is {status}.")
                    logger.debug(f"Download successful.")
                    extension = guess_extension(
                        document.headers.get("content-type", "").split(";")[0]
                    )
                    data_type: str = extension_to_datatype(extension)
                    if data_type != "HTML":
                        return page.url, None, data_type, status, accessed_time
                except Exception as e2:
                    logger.debug(f"Failed to get document type with an error {e2}.")
            case _:
                raise e


def find_images(beautiful_soup: BeautifulSoup) -> set[Image]:
    """
    Gets verified HTML document and finds all images and returns them.
    :param beautiful_soup:  output of BeautifulSoup4 (i.e. validated and parsed HTML)
    """
    logger.debug(f"Finding images on the page.")
    accessed_time = datetime.now()

    # find img tags in DOM
    imgs = beautiful_soup.select("img")
    images = set()
    for img in imgs:
        src = img.attrs.get("src")

        # Extract the path component of the URL
        path = urlparse(src).path
        # Split the path into filename and extension
        filename, extension = os.path.splitext(os.path.basename(path))

        # Parse the URL and check if it has a valid file extension
        if extension is None or extension.lower() not in image_extensions:
            continue

        content_type = extension[1:].upper()
        image: Image = Image(
            filename=filename, content_type=content_type, accessed_time=accessed_time
        )
        images.add(image)
    return images


async def find_sitemap_links(
    current_url: ParseResult,
    robot_file_parser: RobotFileParser,
    domain: str,
    ip: str,
) -> set[str]:
    """
    Checks for sitemap.xml file and recursively traverses the tree to find all URLs.
    :param robot_file_parser: parser for robots.txt
    :param current_url: website url to extract links from
    """
    logger.debug(f"Finding urls from sitemaps.")
    # find URLs from all sitemaps
    # check for sitemap.xml file and return the content as list(), otherwise None
    sitemaps = robot_file_parser.site_maps()
    new_urls_sitemap = set()
    if sitemaps is not None:
        logger.debug(f"Found {len(sitemaps)} sitemaps.")
        for sitemap in sitemaps:
            # parse/fetch found sitemaps and add their URLs
            new_urls_sitemap.update(
                await get_sitemap_urls(
                    sitemap_url=sitemap,
                    domain=domain,
                    ip=ip,
                    robot_delay=robot_file_parser.crawl_delay(useragent=USER_AGENT),
                )
            )
    else:
        # even though sitemap is not in robots.txt, try to find it in root
        sitemap = current_url.scheme + "://" + current_url.netloc + "/sitemap.xml"
        new_urls_sitemap.update(
            await get_sitemap_urls(
                sitemap_url=sitemap,
                domain=domain,
                ip=ip,
                robot_delay=robot_file_parser.crawl_delay(useragent=USER_AGENT),
            )
        )

    # translate URLs to canonical form
    new_urls_sitemap = canonicalize(new_urls_sitemap)

    # check if the url is allowed to visit
    new_urls_sitemap = {
        url
        for url in new_urls_sitemap
        if is_url_allowed(url, robot_file_parser=robot_file_parser)
        and is_domain_allowed(url=url)
    }

    return new_urls_sitemap


async def get_sitemap_urls(
    sitemap_url, domain: str, ip: str, robot_delay: str, new_urls=None
) -> set[str]:
    """
    From given root sitemap url, visiting all .xml child routes and return leaf nodes as a new set of URLs
    This is a recursive function.
    """
    logger.debug(f"Looking at sitemap {sitemap_url} for new urls.")
    # Wait required delay time
    await refresh_site_available_time(domain=domain, ip=ip, robot_delay=robot_delay)
    try:
        sitemap = requests.get(sitemap_url, verify=False, timeout=PAGE_WAIT_TIMEOUT)
        if sitemap.status_code != 200:
            return new_urls if new_urls is not None else set()
        xml = BeautifulSoup(sitemap.content, features="xml")
    except Exception as e:
        logger.debug(f"Failed to parse sitemap with an error {e}.")
        return new_urls if new_urls is not None else set()

    if new_urls is None:
        new_urls = set()

    for loc in xml.find_all("loc"):
        url = loc.get_text()

        if url.endswith(".xml") or "sitemap.xml" in url:
            new_urls.update(
                await get_sitemap_urls(
                    sitemap_url=url, domain=domain, ip=ip, robot_delay=robot_delay
                )
            )
        else:
            new_urls.add(url)

    return new_urls


def extract_binary_links(urls: set) -> (set[str], set[PageData]):
    """
    Extracts all links from a set that point to binary files.
    Returns the original set without binary links and a set of binary entries.
    """
    logger.debug(f"Extracting binary links from found page links.")
    page_data_entries = set()
    urls_to_remove = set()
    for url in urls:
        (binary, data_type) = check_if_binary(url)
        if binary:
            urls_to_remove.add(url)
            page_data: PageData = PageData(data_type_code=data_type)
            page_data_entries.add(page_data)

    urls.difference_update(urls_to_remove)
    return urls, page_data_entries
