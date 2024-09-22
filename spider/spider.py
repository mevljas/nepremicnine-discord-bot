from playwright.async_api import async_playwright

from common.constants import USER_AGENT
from database.database_manager import DatabaseManager
from logger.logger import logger
from services.extract_service import extract
from services.search_service import search
from util.util import block_aggressively


async def run_search(database_manager: DatabaseManager):
    """
    Setups the playwright library and starts the crawler.
    """
    logger.info("Spider started.")
    async with async_playwright() as playwright:
        # Connect to the browser.
        # We need to use a real browser because of Cloudflare protection.
        browser = await playwright.chromium.connect_over_cdp("http://localhost:9222")

        # create a new page.
        browser_page = await browser.new_page()

        # Prevent loading some resources for better performance.
        # await browser_page.route("**/*", block_aggressively)

        # Run the search!
        # await search(
        #     browser_page=browser_page,
        # )
        await browser_page.goto(
            "https://www.nepremicnine.net/oglasi-oddaja/ljubljana-mesto/stanovanje/2-sobno,2.5-sobno,3-sobno,3.5-sobno,4-sobno,4.5-sobno,5-in-vecsobno,apartma/cena-od-300-do-900-eur-na-mesec,velikost-od-30-m2/"
        )

        # await browser_page.pause()

        extracted_data = await extract(browser_page=browser_page)

        await browser_page.close()

    await browser.close()
    logger.info(f"Spider finished.")
