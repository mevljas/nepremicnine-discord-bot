import socket

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
