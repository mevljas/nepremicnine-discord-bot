"""
Database manager module.
"""

import threading
from asyncio import current_task
from datetime import datetime

from sqlalchemy import update, exc
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
    AsyncEngine,
    AsyncSession,
    async_scoped_session,
)

from database.models import meta, Listing, Price
from logger.logger import logger


class DatabaseManager:
    """
    Class for interacting with the database.
    """

    def __init__(self, url: str):
        self.db_connections = threading.local()
        self.url = url

    def async_engine(self) -> AsyncEngine:
        """
        Returns the async engine.
        """
        if not hasattr(self.db_connections, "engine"):
            logger.debug("Getting async engine.")
            self.db_connections.engine = create_async_engine(self.url)
            logger.debug("Creating database engine finished.")
        return self.db_connections.engine

    def async_session_factory(self) -> async_sessionmaker:
        """
        Returns the async session factory.
        :return:
        """
        logger.debug("Getting async session factory.")
        if not hasattr(self.db_connections, "session_factory"):
            engine = self.async_engine()
            self.db_connections.session_factory = async_sessionmaker(bind=engine)
        return self.db_connections.session_factory

    def async_scoped_session(self) -> async_scoped_session[AsyncSession]:
        """
        Returns the async scoped session.
        :return:
        """
        logger.debug("Getting async scoped session.")
        if not hasattr(self.db_connections, "scoped_session"):
            session_factory = self.async_session_factory()
            self.db_connections.scoped_session = async_scoped_session(
                session_factory, scopefunc=current_task
            )
        return self.db_connections.scoped_session

    async def cleanup(self):
        """
        Cleans up the database engine.
        :return:
        """
        logger.debug("Cleaning database engine.")

        await self.db_connections.engine.dispose()
        logger.debug("Cleaning database finished.")

    async def create_models(self):
        """
        Creates all required database tables from the declared models.
        """
        logger.debug("Creating ORM modules.")
        async with self.async_engine().begin() as conn:
            await conn.run_sync(meta.create_all)
        logger.debug("Finished creating ORM modules.")

    async def update_listing(
        self,
        listing_id: int,
        accessed_time: datetime,
        title: str,
        price: float,
        url: str,
    ):
        """
        Updates a listing in the database.
        """
        logger.debug("Updating listing in the database.")
        async with self.async_session_factory()() as session:
            await session.execute(
                update(Listing)
                .where(Listing.id == listing_id)
                .values(
                    accessed_time=accessed_time,
                    title=title,
                    price=price,
                    url=url,
                )
            )
            await session.commit()

            logger.debug("Listing updated.")

    async def save_listing(
        self,
        item_id: str,
        data: tuple[str, str | None, str, float, float, int, str | None, str | None],
    ) -> int:
        """
        Saved a crawled listing to the db.
        """
        logger.debug("Saving new listing %s to the database.", item_id)

        _, _, _, current_price, _, _, _, url = data

        async with self.async_session_factory()() as session:
            try:

                listing = Listing(
                    url=url,
                    accessed_time=datetime.now(),
                    nepremicnine_id=item_id,
                )

                session.add(listing)

                price = Price(accessed_time=datetime.now(), price=current_price)
                session.add(price)
                listing.prices.append(price)

                await session.flush()
                await session.commit()
                logger.debug("New listing saved to the database.")
            except exc.SQLAlchemyError as e:
                await session.rollback()
                logger.warning("Error saving listing to the database with error: %s", e)
                # listing: Listing = (
                #     (
                #         await session.execute(
                #             select(Listing).where(Listing.url == listing.url).limit(1)
                #         )
                #     )
                #     .scalars()
                #     .first()
                # )
