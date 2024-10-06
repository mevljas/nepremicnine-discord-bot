"""Module that contains main spider logic."""

from playwright.async_api import async_playwright

from database.database_manager import DatabaseManager
from logger.logger import logger
from services.extract_service import parse_page


async def run_spider(database_manager: DatabaseManager):
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
            "https://www.nepremicnine.net/oglasi-oddaja/ljubljana-mesto"
            "/stanovanje/2-sobno,2.5-sobno,3-sobno,3.5-sobno,"
            "4-sobno,4.5-sobno,5-in-vecsobno,apartma/cena-od-300"
            "-do-900-eur-na-mesec,velikost-od-30-m2/"
        )

        # await browser_page.pause()

        saved_results = await database_manager.get_listings()

        results = await parse_page(browser_page=browser_page)

        for listing_id, data in results.items():
            logger.debug("Listing ID: %s", listing_id)

            # TODO: this check doesn't work yet.
            if listing_id in saved_results:
                logger.debug("Listing already saved.")

                _, _, _, current_price, _, _, _, url = data

                if saved_results[listing_id] != current_price:
                    logger.debug("New price detected.")
                    await database_manager.add_new_price(
                        listing_id=saved_results[listing_id],
                        current_price=current_price,
                    )

                else:
                    logger.debug("No new price detected.")

                continue

            # We found a new listing.
            logger.debug("New listing found.")
            await database_manager.save_listing(listing_id, data)
        await browser_page.close()

    await browser.close()
    logger.info("Spider finished.")
