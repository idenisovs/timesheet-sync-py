import logging

from fastapi import APIRouter

from timesheet.sync import commands
from timesheet.sync.models import Change

logger = logging.getLogger(__name__)

sync = APIRouter()


@sync.post('/sync')
async def post_sync(changes: list[Change]) -> dict[str, int]:
    logger.info('SYNC endpoint received %d changes', len(changes))
    return commands.sync(changes)
