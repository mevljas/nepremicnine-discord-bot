import asyncio
import logging
import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from database.database_manager import DatabaseManager
from database.models import DataType, PageType, Page
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


async def seed_default(async_session_factory: async_sessionmaker[AsyncSession]):
    """
    Inserts required started data to the database.
    """
    logging.debug("Seeding the database started.")
    async with async_session_factory() as session:
        session.add_all(
            [
                DataType(code="PDF"),
                DataType(code="DOC"),
                DataType(code="DOCX"),
                DataType(code="PPT"),
                DataType(code="PPTX"),
                DataType(code="ZIP"),
                DataType(code="RAR"),
                DataType(code="XLSX"),
                DataType(code="XLSM"),
                DataType(code="UNKNOWN"),
                PageType(code="HTML"),
                PageType(code="BINARY"),
                PageType(code="DUPLICATE"),
                PageType(code="FRONTIER"),
                PageType(code="FAILED"),
                PageType(code="CRAWLING"),
                PageType(code="REDIRECT"),
                Page(url="https://gov.si/", page_type_code="FRONTIER"),
                Page(url="https://evem.gov.si/", page_type_code="FRONTIER"),
                Page(url="https://e-uprava.gov.si/", page_type_code="FRONTIER"),
                Page(url="https://e-prostor.gov.si/", page_type_code="FRONTIER"),
            ]
        )
        await session.commit()
    logging.debug("Seeding the database finished.")


async def main():
    logger.info("Migration started.")

    # Load env variables.
    postgres_user, postgres_password, postgres_db = load_env()

    # Setup database manager.
    database_manager = DatabaseManager(
        url=f"postgresql+asyncpg://"
        f"{postgres_user}:"
        f"{postgres_password}@localhost:5432/"
        f"{postgres_db}"
    )

    # Drop existing tables
    await database_manager.delete_tables()

    # Create database tables.
    await database_manager.create_models()

    # Get database session maker
    async_session_factory = database_manager.async_session_factory()

    await seed_default(async_session_factory)

    # Clean database manager.
    await database_manager.cleanup()
    logger.info("Migration finished.")


if __name__ == "__main__":
    asyncio.run(main())
