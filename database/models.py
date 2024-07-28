import enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Text,
    DateTime,
    LargeBinary,
    MetaData,
    Enum,
)
from sqlalchemy.orm import relationship, declarative_base, Mapped

meta = MetaData(schema="nepremicnine")
Base = declarative_base(metadata=meta)


class ListingType(enum.Enum):
    selling = 1
    renting = 2


class PropertyType(enum.Enum):
    apartment = 1
    house = 2


# A search results table. It stores found apartments and houses.
class Listing(Base):
    __tablename__ = "listing"

    id: Mapped[int] = Column(Integer, primary_key=True)
    url: Mapped[String] = Column(String(3000), unique=True)
    title: Mapped[String] = Column(String(100), unique=False)
    category: Mapped[String] = Column(String(100), unique=False)
    price: Mapped[float] = Column(Integer, unique=False)
    accessed_time = Column(DateTime)
    listing_type: Mapped[Enum[PropertyType]] = Column(Enum(PropertyType), unique=False)
    property_type: Mapped[Enum[ListingType]] = Column(Enum(ListingType), unique=False)
