import asyncio
import os

from dotenv import load_dotenv
from database.database_manager import DatabaseManager
from logger.logger import logger
from spider.spider import start_spider


def load_env() -> (str, str, str, int):
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
    logger.info("Application started.")

    # Load env variables.
    postgres_user, postgres_password, postgres_db = load_env()

    # Setup database manager.
    database_manager = DatabaseManager(
        url=f"postgresql+asyncpg://"
        f"{postgres_user}:"
        f"{postgres_password}@localhost:5432/"
        f"{postgres_db}"
    )

    # Run the spider.
    await start_spider(database_manager=database_manager)

    logger.info("Application finished.")


if __name__ == "__main__":
    asyncio.run(main())
