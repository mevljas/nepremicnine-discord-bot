from bs4 import BeautifulSoup
from playwright.async_api import Page

from logger.logger import logger


async def extract(
    browser_page: Page,
) -> dict[str, str, str, int, int, int, str, str, str]:
    logger.debug(f"Extracting page data...")

    # Reject cookies.
    await browser_page.get_by_role("button", name="Zavrni").click()

    # Wait for the page to load.
    await browser_page.wait_for_load_state("domcontentloaded")

    results = await browser_page.locator(
        '//*[@id="vsebina760"]/div[contains(@class, "seznam")]/div/div/div/div[contains(@class, "col-md-6 col-md-12 position-relative")]'
    ).all()

    # Loop through all the listings.
    extracted_data = dict()
    for item in results:
        image_url = await item.locator(
            'xpath=div/div[contains(@class, "property-image")]/a[2]/img'
        ).get_attribute("src")

        details = item.locator('xpath=div/div[contains(@class, "property-details")]')

        type_data = await details.locator("xpath=span").inner_text()

        listing_type, property_type = type_data.split(":")

        property_type = property_type[1].strip().replace(",", "")

        rooms_count = await details.locator(
            'xpath=span/span[@class="tipi"]'
        ).inner_text()

        url = await details.locator("xpath=a").get_attribute("href")

        title = await details.locator("xpath=a/h2").inner_text()

        description = await details.locator(
            'xpath=p[@itemprop="description"]'
        ).inner_text()

        props = await details.locator(
            'xpath=ul[@itemprop="disambiguatingDescription"]/li'
        ).all()
        size = await props[0].inner_text()
        year = await props[1].inner_text()
        floor = await props[2].inner_text()

        price = await details.locator('xpath=meta[@itemprop="price"]').get_attribute(
            "content"
        )

        item_id = url.split("/")[-2]

        logger.debug(
            f"""
        Title: {title},
        Listing Type: {listing_type},
        Property Type: {property_type},
        Rooms Count: {rooms_count},
        Image URL: {image_url},
        Description: {description},
        Price: {price},
        Size: {size},
        Year: {year},
        Floor: {floor},
        ID: {item_id},
        Url: {url}.
        """
        )

        extracted_data[item_id] = {
            "title": title,
            "image_url": image_url,
            "description": description,
            "price": price,
            "size": size,
            "year": year,
            "floor": floor,
            "url": url,
        }

    logger.info(f"Extracting finished.")

    return extracted_data
