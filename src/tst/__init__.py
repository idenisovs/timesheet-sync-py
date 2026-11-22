from importlib.metadata import version

from fastapi import FastAPI

from .healthcheck import healthcheck_api
from .sync import sync_api

app = FastAPI(version=version('timesheet-sync-py'))

app.include_router(healthcheck_api)
app.include_router(sync_api)


@app.get('/')
def hello() -> dict[str, str]:
    return {'message': 'Hello from timesheet-sync-py!'}
