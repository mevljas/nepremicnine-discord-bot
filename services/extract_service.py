"""Module that contains data extraction logic."""

from playwright.async_api import Page, Locator

from logger.logger import logger


async def parse_page(
    browser_page: Page,
) -> dict[str, tuple[str, str | None, str, float, float, int, str | None, str | None]]:
    """Parses the page and extracts data."""

    logger.debug("Parsing page...")

    # Reject cookies.
    await browser_page.get_by_role("button", name="Zavrni").click()

    # Wait for the page to load.
    await browser_page.wait_for_load_state("domcontentloaded")

    results = await browser_page.locator(
        """//*[@id="vsebina760"]/div[contains(@class, "seznam")]
        /div/div/div/div[contains(@class, "col-md-6 col-md-12 position-relative")]"""
    ).all()

    # Loop through all the listings.
    extracted_data = {}
    for result in results:
        item_id, data = await parse_result(result)
        extracted_data[item_id] = data

    logger.info("Extracting finished.")

    return extracted_data


async def parse_result(
    item: Locator,
) -> tuple[str, tuple[str, str | None, str, float, float, int, str | None, str | None]]:
    """Extracts data from the result."""

    logger.debug("Extracting result data...")

    image_url = await item.locator(
        'xpath=div/div[contains(@class, "property-image")]/a[2]/img'
    ).get_attribute("src")

    details = item.locator('xpath=div/div[contains(@class, "property-details")]')

    listing_type, property_type = (
        await details.locator("xpath=span").inner_text()
    ).split(":")

    property_type = property_type[1].strip().replace(",", "")

    rooms_count = await details.locator('xpath=span/span[@class="tipi"]').inner_text()

    url = await details.locator("xpath=a").get_attribute("href")

    title = await details.locator("xpath=a/h2").inner_text()

    description = await details.locator('xpath=p[@itemprop="description"]').inner_text()

    props = await details.locator(
        'xpath=ul[@itemprop="disambiguatingDescription"]/li'
    ).all()
    size = float((await props[0].inner_text()).split(" ")[0].replace(",", "."))
    year = int(await props[1].inner_text())

    floor = await props[2].inner_text() if len(props) > 2 else None

    price = float(
        await details.locator('xpath=meta[@itemprop="price"]').get_attribute("content")
    )

    item_id = url.split("/")[-2]

    logger.debug(
        """
    Title: %s,
    Listing Type: %s,
    Property Type: %s,
    Rooms Count: %s,
    Image URL: %s,
    Description: %s,
    Price: %f,
    Size: %s,
    Year: %d,
    Floor: %s,
    ID: %s,
    Url: %s.
    """,
        title,
        listing_type,
        property_type,
        rooms_count,
        image_url,
        description,
        price,
        size,
        year,
        floor,
        item_id,
        url,
    )

    logger.info("Extracting finished.")

    return item_id, (
        title,
        image_url,
        description,
        price,
        size,
        year,
        floor,
        url,
    )
