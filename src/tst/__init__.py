import logging
from contextlib import asynccontextmanager
from importlib.metadata import version

from fastapi import FastAPI

from .healthcheck import healthcheck_api
from .sync import sync_api


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    )
    yield


app = FastAPI(version=version('timesheet-sync-py'), lifespan=lifespan)

app.include_router(healthcheck_api)
app.include_router(sync_api)


@app.get('/')
def hello() -> dict[str, str]:
    return {'message': 'Hello from timesheet-sync-py!'}
