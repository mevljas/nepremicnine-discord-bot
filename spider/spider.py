from playwright.async_api import async_playwright

from common.constants import USER_AGENT
from database.database_manager import DatabaseManager
from logger.logger import logger
from services.search_service import search
from util.util import block_aggressively


async def run_search(database_manager: DatabaseManager):
    """
    Setups the playwright library and starts the crawler.
    """
    logger.info("Spider started.")
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=False,
            args=[
                "--ignore-certificate-errors",
                "--ignore-urlfetcher-cert-requests",
                "--ignore-certificate-errors",
                "--allow-running-insecure-content",
                "--ignore-certificate-errors-spki-lis",
            ],
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

        # Run the search!
        await search(
            browser_page=browser_page,
        )

        await browser_page.close()

    await browser.close()
    logger.info(f"Spider finished.")
