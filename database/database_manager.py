import threading
from asyncio import current_task
from datetime import datetime

from sqlalchemy import select, Result, update, exc, delete, Enum
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
    AsyncEngine,
    AsyncSession,
    async_scoped_session,
)
from sqlalchemy.sql.functions import func

from database.models import meta, Frontier, Listing, PropertyType, ListingType
from logger.logger import logger


class DatabaseManager:
    def __init__(self, url: str):
        self.db_connections = threading.local()
        self.url = url

    def async_engine(self) -> AsyncEngine:
        if not hasattr(self.db_connections, "engine"):
            logger.debug("Getting async engine.")
            self.db_connections.engine = create_async_engine(self.url)
            logger.debug("Creating database engine finished.")
        return self.db_connections.engine

    def async_session_factory(self) -> async_sessionmaker:
        logger.debug("Getting async session factory.")
        if not hasattr(self.db_connections, "session_factory"):
            engine = self.async_engine()
            self.db_connections.session_factory = async_sessionmaker(bind=engine)
        return self.db_connections.session_factory

    def async_scoped_session(self) -> async_scoped_session[AsyncSession]:
        logger.debug("Getting async scoped session.")
        if not hasattr(self.db_connections, "scoped_session"):
            session_factory = self.async_session_factory()
            self.db_connections.scoped_session = async_scoped_session(
                session_factory, scopefunc=current_task
            )
        return self.db_connections.scoped_session

    async def cleanup(self):
        logger.debug("Cleaning database engine.")
        """
        Cleanup database engine.    
        """
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

    async def delete_tables(self):
        """
        Deletes all tables from the database.
        """
        logger.debug("Deleting database tables.")
        async with self.async_engine().begin() as conn:
            await conn.run_sync(meta.reflect)
            await conn.run_sync(meta.drop_all)
        logger.debug("Finished deleting database tables.")

    async def pop_frontier(self) -> tuple[int, str]:
        """
        Pops the first page off the frontier.
        """
        logger.debug("Getting the top of the frontier.")
        async with self.async_session_factory()() as session:
            frontier: Frontier = (
                (await session.execute(select(Frontier).limit(1).with_for_update()))
                .scalars()
                .first()
            )
            logger.debug("Got the top of the frontier.")
            if frontier is not None:
                page_id, page_url = frontier.id, frontier.url
                await session.execute(
                    update(Frontier)
                    .where(Frontier.id == Frontier.id)
                    .values(page_type_code="CRAWLING")
                )
                await session.commit()
                return page_id, page_url
            logger.debug("Frontier is empty")

    async def get_frontier_links(self) -> set[str]:
        """
        Gets all links from the frontier.
        """
        logger.debug("Getting links from the frontier.")
        async with self.async_session_factory()() as session:
            result: Result = await session.execute(select(Frontier.url))
            logger.debug("Got links from the frontier.")

            return set([url for url in result.scalars()])

    async def remove_from_frontier(self, page_id: int):
        """
        Removes a link from frontier.
        """
        logger.debug("Removing a link from the frontier.")
        async with self.async_session_factory()() as session:
            await session.execute(delete(Frontier).where(Frontier.id == page_id))
            await session.commit()

            logger.debug("Link removed from the frontier.")

    async def add_to_frontier(self, link: str):
        """
        Adds a new link to the frontier.
        """
        logger.debug("Adding a link to the frontier.")
        async with self.async_session_factory()() as session:
            try:
                page: Frontier = Frontier(url=link)
                session.add(page)
                await session.flush()
                page_id = page.id
                await session.commit()
                logger.debug("Added link to the frontier.")
                return page_id
            except exc.IntegrityError:
                await session.rollback()
                logger.debug("Adding link failed because its already in the frontier.")
                return None

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
                    # TODO: Keep file history in another db.
                    price=price,
                    url=url,
                )
            )
            await session.commit()

            logger.debug("Listing updated.")

    async def save_listing(
        self,
        listing: Listing,
    ) -> int:
        """
        Saved a crawled listing to the db.
        """
        logger.debug("Saving new listing to the database.")
        listing_id: int
        async with self.async_session_factory()() as session:
            try:
                session.add(listing)
                await session.flush()
                listing_id = listing.id
                await session.commit()
                logger.debug(f"New listing saved to the database.")
            except exc.IntegrityError:
                await session.rollback()
                logger.debug(
                    "Adding listing failed because it already exists in the database."
                )
                listing: Listing = (
                    (
                        await session.execute(
                            select(Listing).where(Listing.url == listing.url).limit(1)
                        )
                    )
                    .scalars()
                    .first()
                )
                listing_id = listing.id
            return listing_id
