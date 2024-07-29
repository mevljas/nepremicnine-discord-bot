import re
import socket
from urllib.parse import ParseResult
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from url_normalize import url_normalize
from w3lib.url import url_query_cleaner

from common.constants import (
    USER_AGENT,
    excluded_resource_types,
)
from logger.logger import logger


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
