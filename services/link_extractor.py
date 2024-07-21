import re
from urllib.parse import ParseResult
from urllib.robotparser import RobotFileParser

from bs4 import BeautifulSoup

from common.constants import navigation_assign_regex, navigation_func_regex
from logger.logger import logger
from util.util import is_url, fill_url, is_url_allowed, is_domain_allowed, canonicalize


def find_links(
    beautiful_soup: BeautifulSoup,
    current_url: ParseResult,
    robot_file_parser: RobotFileParser,
) -> set[str]:
    """
    Get's verified HTML document and finds all valid new URL holder elements, parses those URLs and returns them.
    :param robot_file_parser: parser for robots.txt
    :param current_url: website url to extract links from
    :param beautiful_soup:  output of BeautifulSoup4 (i.e. validated and parsed HTML)
    """
    logger.debug(f"Finding links on the page.")

    # find new URLs in DOM
    # select all valid navigatable elements
    clickables = beautiful_soup.select("a, [onclick]")
    new_urls = set()
    for element in clickables:
        url = None
        # check if current element is basic anchor tag or element with onclick listener
        href = element.attrs.get("href")
        onclick = element.attrs.get("onclick")
        if href is not None and is_url(href):
            url = href
        elif onclick is not None:
            # check for format when directly assigning
            if navigation_assign_regex.match(onclick):
                url = re.search(navigation_assign_regex, onclick).group(3)
            # check for format when using function to assign
            elif navigation_func_regex.match(onclick):
                url = re.search(navigation_func_regex, onclick).group(4)
        else:
            continue

        # continue if no valid url was found
        if url is None:
            continue

        # handle relative path URLs and fix them
        url = fill_url(url, current_url)

        # check if the url is allowed to visit
        if is_url_allowed(
            url, robot_file_parser=robot_file_parser
        ) and is_domain_allowed(url=url):
            new_urls.add(url)

    # translate URLs to canonical form
    new_urls = canonicalize(new_urls)

    return new_urls
