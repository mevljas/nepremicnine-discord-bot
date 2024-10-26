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

    # List of new listings to send to Discord.
    discord_listings = []

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

        for nepremicnine_id, new_data in results.items():
            logger.debug("Listing ID: %s", nepremicnine_id)

            if nepremicnine_id in saved_results:
                logger.debug("Listing already saved.")

                _, _, _, new_price, _, _, _, _ = new_data

                listing_id, old_prices = saved_results[nepremicnine_id]

                if old_prices[-1] != new_price:
                    logger.info("New saved_price detected for %s.", nepremicnine_id)
                    await database_manager.add_new_price(
                        listing_id=listing_id,
                        current_price=new_price,
                    )

                    print("New data before merging: ", new_data)

                    # Merge old and new prices.
                    old_prices.append(new_price)
                    new_data = new_data[:3] + (old_prices,) + new_data[4:]

                    print("New data after merging: ", new_data)

                    discord_listings.append(new_data)

                else:
                    logger.debug("No new saved_price detected.")

                continue

            # We found a new listing.
            logger.info("New listing found %s.", nepremicnine_id)

            await database_manager.save_listing(nepremicnine_id, new_data)

            # Convert price to a list of prices
            new_data = new_data[:3] + ([new_data[3]],) + new_data[4:]
            discord_listings.append(new_data)
        await browser_page.close()

    await browser.close()
    logger.info("Spider finished. Found %d new listings.", len(discord_listings))

    return discord_listings
