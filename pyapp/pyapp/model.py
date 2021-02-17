from sqlalchemy import create_engine, select, update, \
    Table, Column, Integer, String, ForeignKey, and_
from sqlalchemy.orm import registry, relationship, Session
from dataclasses import dataclass, field
from typing import List, Optional
from collections.abc import Iterable
import os
import hashlib
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

def record_visit(path, ip_address, user_agent, name):
    "Record a visit to a path and return the number of visits by this fingerprint"
    fingerprint = hashlib.sha256(
        f"{ip_address}-{user_agent}-{name}".encode("utf-8")).hexdigest()
    with session() as s:
        # Find the existing record of visits to this path by this fingerprint:
        r = s.execute(VisitsRecord.search(path, fingerprint)).first()
        if r is None:
            # Initialize the very first visit to this path by this fingerprint
            r = VisitsRecord(path=path, user_fingerprint=fingerprint, visits=1)
            s.add(r)
        else:
            # Add to the pagecount of this path for this fingerprint:
            s.execute(VisitsRecord.visit(path, fingerprint))
            # Retrieve the new record:
            r = s.execute(VisitsRecord.search(path, fingerprint)).first()[0]
        log.info(f"Visit: path={path} r={r}")
        s.commit()
        # Return the # of times this path has been accessed by this fingerprint
        return r.visits

mapper_registry.metadata.create_all()
