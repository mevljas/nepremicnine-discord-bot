"""Module that contains main application logic."""

import asyncio

from dotenv import load_dotenv

from database.database_manager import DatabaseManager
from logger.logger import logger
from spider.spider import run_spider


def load_env() -> (str, str, str, int):
    """
    Load ENV variables.
    :return: postgres_user, postgres_password, postgres_db
    """
    load_dotenv()
    # return postgres_user, postgres_password, postgres_db


async def main():
    """
    Main function.
    :return:
    """
    logger.info("Application started.")

    # Load env variables.
    # postgres_user, postgres_password, postgres_db = load_env()

    # Setup database manager.
    database_manager = DatabaseManager(
        url="sqlite+aiosqlite:///nepremicnine_database.sqlite"
    )

    # Run the spider.
    await run_spider(database_manager=database_manager)

    logger.info("Application finished.")


if __name__ == "__main__":
    asyncio.run(main())
