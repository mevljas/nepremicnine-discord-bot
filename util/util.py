import re
import socket
from urllib.parse import ParseResult
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from url_normalize import url_normalize
from w3lib.url import url_query_cleaner

from common.constants import (
    full_url_regex,
    USER_AGENT,
    binary_file_extensions,
    govsi_regex,
    excluded_resource_types,
)
from logger.logger import logger
from services.docoument_extractor import extension_to_datatype


def canonicalize(urls: set) -> set[str]:
    """
    Translates URLs into canonical form
    - adds missing schema, host, fix encodings, etc.
    - remove query parameters
    - remove element id selector from end of URL
    """
    logger.debug(f"Translating urls into a canonical form.")
    new_urls = set()
    for url in urls:
        u = url_normalize(url)  # general form fixes
        u = url_query_cleaner(u)  # remove query params
        u = re.sub(r"#.*$", "", u)  # remove fragment
        # end with / if not a filetype
        if not (has_file_extension(u) or u.endswith("/")):
            u += "/"
        new_urls.add(u)
    return new_urls


def has_file_extension(url) -> bool:
    """
    Checks if URL end with a file extension like: .html, .pdf, .txt, etc.
    """
    logger.debug(f"Checking whether url {url} points to file.")
    pattern = r"^.*\/[^\/]+\.[^\/]+$"
    return bool(re.match(pattern, url))


def is_url_allowed(url: str, robot_file_parser: RobotFileParser) -> bool:
    """
    Checks if URL is allowed in page's robots.txt
    """
    logger.debug(f"Checking whether url {url} is allowed in robots.txt.")
    if robot_file_parser is None:
        allowed = True
    else:
        allowed = robot_file_parser.can_fetch(USER_AGENT, url)
    logger.debug(f"Url {url} allowed in robots.txt: {allowed}.")
    return allowed


def is_url(url) -> bool:
    """
    Checks if string is URL. It should return true for full URLs and also for partial (e.g. /about/me, #about, etc.)
    """
    logger.debug(f"Checking whether potential url {url} is of valid format.")
    if url is None:
        return False
    try:
        result = urlparse(url)
        if result.scheme and result.scheme not in ["http", "https"]:
            return False
        return bool(result.netloc or result.path or result.fragment)
    except:
        return False


def check_if_binary(url: str) -> (bool, str):
    """
    Check if url leads to binary file
    """
    for extension in binary_file_extensions:
        if url.endswith(extension):
            logger.debug(f"Url {url} leads to binary file.")
            data_type: str = extension_to_datatype(extension)
            return True, data_type

    logger.debug(f"Url {url} does not lead to a binary file.")
    return False, None


def fill_url(url: str, current_url_parsed: ParseResult) -> str:
    """
    Parameter url could be a full url or just a relative path (e.g. '/users/1', 'about.html', '/home')
    In such cases fill the rest of the URL and return
    """
    logger.debug(f"Filling url {url}.")
    url_parsed = urlparse(url)
    filled_url = url
    # check if full url
    if not url_parsed.scheme or not url_parsed.netloc:
        # take URL data from current page and append relative path
        filled_url = current_url_parsed.scheme + "://" + current_url_parsed.netloc + url
    return filled_url


def get_real_url_from_shortlink(url: str) -> str:
    """
    Gets the full URL that is return by server in case of shortened URLs with missing schema and host, etc.
    'gov.si' -> 'https://www.gov.si'
    """
    logger.debug(f"Getting real url from the short url {url}.")
    try:
        resp = requests.get(url)
    except:
        return url
    return resp.url


def is_domain_allowed(url: str) -> bool:
    """
    Checks whether the domain is on the allowed list.
    """
    logger.debug(f"Checking whether {url} is on the domain allowed list.")
    url_parsed = urlparse(url)
    allowed = govsi_regex.match(url_parsed.netloc)
    logger.debug(f"Url {url} domain allowed: {allowed}.")
    return bool(allowed)


def fix_shortened_url(url: str) -> str:
    """
    Fix shortened url if necessary.
    Also transform into canonical form to then compare to actual url in browser.
    """
    if not full_url_regex.match(url):
        logger.debug("Url has to be cleaned.")
        return get_real_url_from_shortlink(url=url)
    logger.debug("Url doesnt have to be cleaned.")
    return url


async def block_aggressively(route):
    """
    Prevent loading some resources for better performance.
    """
    if route.request.resource_type in excluded_resource_types:
        await route.abort()
    else:
        await route.continue_()


def get_site_ip(hostname: str):
    """
    Returns site's ip address.
    """
    try:
        return socket.gethostbyname(hostname)
    except:
        logger.warning(f"Getting site ip address failed.")
        return None
