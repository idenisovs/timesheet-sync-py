from fastapi import APIRouter

sync_api = APIRouter()


@sync_api.post('/sync')
def sync() -> dict[str, str]:
    return {'message': 'ok'}
