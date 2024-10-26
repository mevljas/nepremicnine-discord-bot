# pylint: disable=too-few-public-methods
"""
This module contains the SQLAlchemy models for the database.
"""

import enum
from typing import List

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    MetaData,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, Mapped, relationship

meta = MetaData()
Base = declarative_base(metadata=meta)


class ListingType(enum.Enum):
    """
    Enum for listing type.
    Currently not used.
    """

    SELLING = 1
    RENTING = 2


class PropertyType(enum.Enum):
    """
    Enum for property type.
    Currently not used.
    """

    APARTMENT = 1
    HOUSE = 2


class Listing(Base):
    """
    A search results table. It stores found apartments and houses.
    """

    __tablename__ = "listing"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    nepremicnine_id: Mapped[str] = Column(String(50), unique=True)
    url: Mapped[str] = Column(String(150), unique=True)
    accessed_time = Column(DateTime)
    prices: Mapped[List["Price"]] = relationship(lazy="selectin")


class Price(Base):
    """
    A table that stores the current and previous prices.
    """

    __tablename__ = "price"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    price: Mapped[float] = Column(Integer, unique=False)
    accessed_time = Column(DateTime)
    listing_id: Mapped[int] = Column(ForeignKey("listing.id"))
