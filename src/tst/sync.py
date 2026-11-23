from fastapi import APIRouter

from .models.change import Change

sync_api = APIRouter()


@sync_api.post('/sync')
def sync(changes: list[Change]) -> dict[str, str]:
    return {'message': 'ok'}
