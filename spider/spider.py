# pylint: disable=too-many-locals
"""Module that contains main spider logic."""
from asyncio import sleep
from collections import defaultdict


from playwright.async_api import async_playwright

from database.database_manager import DatabaseManager
from logger.logger import logger
from services.extract_service import parse_page


async def run_spider(database_manager: DatabaseManager) -> tuple[dict, bool]:
    """
    Setups the playwright library and runs the crawler.
    Returns a dictionary with listings and a boolean indicating if an error occurred.
    """
    logger.info("Spider started.")

    # Dictionary to store the listings. Key is the channel name.
    discord_listings = defaultdict(list)

    async with async_playwright() as playwright:
        # Connect to the browser.
        browser = await playwright.chromium.launch(headless=False)

        # Read page urls from a config file.
        config = await read_config()

        saved_results = await database_manager.get_listings()

        error = False

        # For each url, send the results to a different channel.
        for channel, page_url in config:
            logger.debug("Processing channel %s with URL %s", channel, page_url)

            # create a new page inside context.
            browser_page = await browser.new_page(
                # pylint: disable=line-too-long
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
            )

            # Prevent loading some resources for better performance.
            # await browser_page.route("**/*", block_aggressively)

            logger.debug("Navigating to %s", page_url)
            await browser_page.goto(page_url)

            # await browser_page.pause()

            more_pages = True

            index = 1

            results = {}

            while more_pages:
                if index > 1:
                    # Close the previous page.
                    await browser_page.close()

                    # create a new page.
                    browser_page = await browser.new_page()

                    await browser_page.goto(f"{page_url}{index}/")

                try:
                    results_tmp, more_pages = await parse_page(
                        browser_page=browser_page
                    )
                    results.update(results_tmp)
                except Exception as e:  # pylint: disable=broad-except
                    logger.error("Error parsing page: %s", e)
                    error = True
                index += 1

                await sleep(60)  # Sleep for 1 minute to avoid being blocked.

            for nepremicnine_id, new_data in results.items():
                logger.debug("Listing ID: %s", nepremicnine_id)

                if nepremicnine_id in saved_results:
                    logger.debug("Listing already saved.")

                    _, _, _, new_price, _, _, _, _ = new_data

                    listing_id, old_prices = saved_results[nepremicnine_id]

                    if old_prices[-1] != new_price:
                        logger.debug(
                            "New saved_price detected for %s.", nepremicnine_id
                        )
                        await database_manager.add_new_price(
                            listing_id=listing_id,
                            current_price=new_price,
                        )

                        # Merge old and new prices.
                        old_prices.append(new_price)
                        new_data = new_data[:3] + (old_prices,) + new_data[4:]

                        discord_listings[channel].append(new_data)

                    else:
                        logger.debug("No new saved_price detected.")

                    continue

                # We found a new listing.
                logger.debug("New listing found %s.", nepremicnine_id)

                await database_manager.save_listing(nepremicnine_id, new_data)

                # Convert price to a list of prices
                new_data = new_data[:3] + ([new_data[3]],) + new_data[4:]
                discord_listings[channel].append(new_data)
            await browser_page.close()

    await browser.close()

    # Count all listings in discord_listings.
    total_listings = sum(len(listings) for listings in discord_listings.values())

    logger.info("Spider finished. Found %d new listings.", total_listings)

    return discord_listings, error


async def read_config():
    """
    Read the config file.
    Each line in the file contains a channel name and a URL.
    """
    with open("config.txt", encoding="utf-8") as file:
        return [line.strip().split() for line in file.readlines()]
