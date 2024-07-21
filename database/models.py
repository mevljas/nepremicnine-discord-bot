from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Text,
    DateTime,
    LargeBinary,
    MetaData,
)
from sqlalchemy.orm import relationship, declarative_base, Mapped

meta = MetaData(schema="crawldb")
Base = declarative_base(metadata=meta)


class Page(Base):
    __tablename__ = "page"

    id: Mapped[int] = Column(Integer, primary_key=True)
    url: Mapped[String] = Column(String(3000), unique=True)
    title: Mapped[String] = Column(String(100), unique=False)
    accessed_time = Column(DateTime)
