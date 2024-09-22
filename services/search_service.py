from playwright.async_api import Page

from logger.logger import logger


async def search(
    browser_page: Page,
) -> set[str]:
    logger.debug(f"Searching with parameters...")

    # TODO: We don't really have to input all this data, because we can just use the URL.
    # https://www.nepremicnine.net/oglasi-oddaja/ljubljana-mesto/stanovanje/2.5-sobno,3-sobno,3.5-sobno,4-sobno,4.5-sobno,5-in-vecsobno,apartma/cena-od-300-do-900-eur-na-mesec,velikost-od-30-m2/

    # Go to the nepremicnine.net advance search.
    await browser_page.goto("https://www.nepremicnine.net/nepremicnine.html")

    # Reject cookies.
    await browser_page.get_by_role("button", name="Zavrni").click()

    # Select "Slovenia" country.
    await browser_page.locator("#NNd197").check()

    # Select "LJ-mesto" region.
    await browser_page.locator(
        '//div[@id="regue"]//div[@id="NNmap"]/div/*[name()="svg"]/*[name()="g"]/*[name()="path"][13]'
    ).click()

    # Select listing type.
    await browser_page.locator("#NNsearch").get_by_text("Oddaja").click()

    # Select "stanovanje" property type.
    await browser_page.locator("#NNsearch").get_by_text("Stanovanje").click()

    # Apply filters
    await browser_page.get_by_text("2-sobno", exact=True).click()
    await browser_page.get_by_text("4-sobno").click()
    await browser_page.get_by_text("2,5-sobno", exact=True).click()
    await browser_page.get_by_text("4,5-sobno").click()
    await browser_page.get_by_text("3-sobno", exact=True).click()
    await browser_page.get_by_text("in večsobno").click()
    await browser_page.get_by_text("3,5-sobno").click()
    await browser_page.get_by_text("Apartma").click()

    # Price
    # Minimum price
    await browser_page.locator("#NNc1").fill("300")

    # Maximum price
    await browser_page.locator("#NNc2").fill("900")

    # Minimum size
    await browser_page.locator("#NNm1").fill("30")
    logger.info(f"Search finished.")

    # Submit.
    await browser_page.get_by_role("button", name="Prikaži rezultate").click()
