"""
Module for setting up the database.
"""

import asyncio
import os

from dotenv import load_dotenv

from database.database_manager import DatabaseManager
from logger.logger import logger


def load_env() -> (str, str, str):
    """
    Load ENV variables.
    :return: postgres_user, postgres_password, postgres_db
    """
    load_dotenv()
    postgres_user = os.getenv("POSTGRES_USER")
    postgres_password = os.getenv("POSTGRES_PASSWORD")
    postgres_db = os.getenv("POSTGRES_DB")
    return postgres_user, postgres_password, postgres_db


async def main():
    """
    Main function.
    :return:
    """
    logger.info("DB setup started.")

    # Load env variables.
    # postgres_user, postgres_password, postgres_db = load_env()

    # Delete existing database if it exists.
    if os.path.exists("nepremicnine_database.sqlite"):
        os.remove("nepremicnine_database.sqlite")

    # Setup database manager.
    database_manager = DatabaseManager(
        url="sqlite+aiosqlite:///nepremicnine_database.sqlite"
    )

    # Create database tables.
    await database_manager.create_models()

    # Clean database manager.
    await database_manager.cleanup()
    logger.info("DB setup finished.")


if __name__ == "__main__":
    asyncio.run(main())
