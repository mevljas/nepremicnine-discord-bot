from playwright.async_api import Page

from logger.logger import logger


async def search(
    browser_page: Page,
) -> set[str]:
    logger.debug(f"Searching with parameters...")

    # Go to the nepremicnine website.
    await browser_page.goto("https://www.nepremicnine.net")

    # Select listing type.
    await browser_page.locator("#NOp").select_option("Oddaja")

    # Select property type.
    await browser_page.locator("#NOn").select_option("Hiša")

    # Select region.
    await browser_page.locator("#NOr").select_option("LJ-okolica")

    logger.info(f"Search finished.")
