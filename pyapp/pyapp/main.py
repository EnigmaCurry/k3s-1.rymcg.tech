from fastapi import FastAPI, Header
from typing import Optional
import model
import logging
import hashlib

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)
app = FastAPI()

def record_visit(path, ip_address, user_agent, name):
    fingerprint = hashlib.sha256(
        f"{ip_address}-{user_agent}-{name}".encode("utf-8")).hexdigest()
    with model.session() as s:
        r = s.execute(model.VisitsRecord.search(path, fingerprint)).first()
        if r is None:
            r = model.VisitsRecord(path=path, user_fingerprint=fingerprint, visits=1)
            s.add(r)
        else:
            s.execute(model.VisitsRecord.visit(path, fingerprint))
            r = s.execute(model.VisitsRecord.search(path, fingerprint)).first()[0]
        log.info(f"Visit: path={path} r={r}")
        s.commit()
        return r.visits

@app.get("/")
async def root(x_real_ip: str = Header(None),
               user_agent: str = Header(None),
               name: Optional[str] = None):
    num_visits = record_visit("/", x_real_ip, user_agent, name)
    greet = "Hi there" if name is None else f"Hi {name}"
    if num_visits == 1:
        return dict(
            message=f"{greet}, this must be your first time visiting this page")
    else:
        return dict(
            message=f"{greet}, you have visited this page {num_visits} times.")
