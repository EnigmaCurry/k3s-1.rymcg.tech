from sqlalchemy import create_engine, select, \
    Table, Column, Integer, String, ForeignKey
from sqlalchemy.orm import registry, relationship, Session
from dataclasses import dataclass, field
from typing import List, Optional
from collections.abc import Iterable
import os
import logging

log = logging.getLogger(__name__)

def get_connection_string():
    """Find the database connection string from environment variables.

    If DB_CONNECTION is set, use it as the full sqlalchemy connection string.
    Otherwise find standard PostgreSQL environment variables:
    """
    try:
        return os.environ["DB_CONNECTION"]
    except KeyError:
        log.warn("No DB_CONNECTION variable set, "
                 "trying to construct a PostgreSQL connection string ...")
        try:
            PGUSER=os.environ['PGUSER']
            PGPASSWORD=os.environ['PGPASSWORD']
            PGHOST=os.environ['PGHOST']
            PGDATABASE=os.environ['PGDATABASE']
            return f"postgresql+psycopg2://" \
                f"{PGUSER}:{PGPASSWORD}@{PGHOST}/{PGDATABASE}"
        except KeyError:
            log.error("Could not construct a PostgreSQL connection string: "
                      "missing variables: PGUSER, PGPASSWORD, "
                      "PGHOST, PGDATABASE")
            raise

DB_CONNECTION=get_connection_string()
engine = create_engine(DB_CONNECTION, echo=False, future=True)

mapper_registry = registry()
mapper_registry.metadata.bind = engine
def session():
    return Session(engine)


@mapper_registry.mapped
@dataclass
class ImageRecord:
    __table__ = Table(
        "image",
        mapper_registry.metadata,
        Column("url", String(2000), primary_key=True),
        Column("path", String(500)),
        Column("source", String(50), ForeignKey("image_source.name")),
    )
    url: str
    path: str
    source: str

    @classmethod
    def search(cls, search_term: str, source: str = None):
        q = select(ImageRecord).join(ImageSource.images)
        if source:
            q = q.where(ImageSource.name == source)
        return q
