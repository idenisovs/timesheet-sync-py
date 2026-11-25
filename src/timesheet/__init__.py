import logging
from contextlib import asynccontextmanager
from importlib.metadata import version

from fastapi import FastAPI

from timesheet.healthckeck.api import healthcheck
from timesheet.sync.api import sync


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    )
    yield


app = FastAPI(version=version('timesheet-sync-py'), lifespan=lifespan)

app.include_router(healthcheck)
app.include_router(sync)


@app.get('/')
def hello() -> dict[str, str]:
    return {'message': 'Hello from timesheet-sync-py!'}
