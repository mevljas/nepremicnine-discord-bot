"""
This module contains the SQLAlchemy models for the database.
"""

import enum
from typing import Set

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    MetaData,
)
from sqlalchemy.orm import declarative_base, Mapped, relationship

meta = MetaData()
Base = declarative_base(metadata=meta)


class ListingType(enum.Enum):
    """
    Enum for listing type.
    """

    SELLING = 1
    RENTING = 2


class PropertyType(enum.Enum):
    """
    Enum for property type.
    """

    APARTMENT = 1
    HOUSE = 2


class Listing(Base):
    """
    A search results table. It stores found apartments and houses.
    """

    __tablename__ = "listing"

    id: Mapped[str] = Column(Integer, primary_key=True)
    url: Mapped[str] = Column(String(3000), unique=True)
    accessed_time = Column(DateTime)
    history: Mapped[Set["History"]] = relationship(back_populates="listing")


class History(Base):
    """
    A table that stores the history of the listings.
    """

    __tablename__ = "history"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    price: Mapped[float] = Column(Integer, unique=False)
    accessed_time = Column(DateTime)
