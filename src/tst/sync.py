import logging

from fastapi import APIRouter

from .models.change import Change

logger = logging.getLogger(__name__)

sync_api = APIRouter()

@sync_api.post('/sync')
def sync(changes: list[Change]) -> dict[str, str]:
    logger.info('SYNC endpoint received %d changes', len(changes))

    return {'message': 'ok'}
