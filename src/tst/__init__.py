from contextlib import asynccontextmanager
from importlib.metadata import version
from pathlib import Path

from fastapi import FastAPI

from .healthcheck import healthcheck_api
from .sync import sync_api


@asynccontextmanager
async def lifespan(_app: FastAPI):
    entities = Path('entities.tsv')

    if not entities.exists():
        entities.touch()

    yield


app = FastAPI(version=version('timesheet-sync-py'), lifespan=lifespan)

app.include_router(healthcheck_api)
app.include_router(sync_api)


@app.get('/')
def hello() -> dict[str, str]:
    return {'message': 'Hello from timesheet-sync-py!'}
