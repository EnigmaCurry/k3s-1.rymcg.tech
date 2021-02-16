from sqlalchemy import create_engine, select, update, \
    Table, Column, Integer, String, ForeignKey, and_
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
class VisitsRecord:
    __table__ = Table(
        "visits",
        mapper_registry.metadata,
        Column("path", String(2000), primary_key=True),
        Column("user_fingerprint", String(500), primary_key=True),
        Column("visits", Integer, default=0)
    )
    path: str
    user_fingerprint: str
    visits: int

    @classmethod
    def search(cls, path: str, user_fingerprint: str):
        return select(VisitsRecord).where(and_(
            VisitsRecord.path == path,
            VisitsRecord.user_fingerprint == user_fingerprint))

    @classmethod
    def visit(cls, path: str, user_fingerprint: str):
        return update(VisitsRecord).where(and_(
            VisitsRecord.path == path,
            VisitsRecord.user_fingerprint == user_fingerprint
        )).values(visits=VisitsRecord.visits + 1)

mapper_registry.metadata.create_all()
