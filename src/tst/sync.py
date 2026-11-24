import logging
from datetime import UTC, datetime

from fastapi import APIRouter

from .models.change import Change

logger = logging.getLogger(__name__)

sync_api = APIRouter()

entities_by_id = {}


@sync_api.post('/sync')
def sync(changes: list[Change]) -> dict[str, int]:
    logger.info('SYNC endpoint received %d changes', len(changes))

    skipped = 0
    applied = 0

    for change in changes:
        if change.entity != 'activity':
            logger.warning(f'Skipping {change.entity}!')
            skipped += 1
            continue

        snapshot = change.after if change.after is not None else change.before

        if not snapshot:
            logger.warning(f'Change {change.id} is missing both snapshots!')
            skipped += 1
            continue

        entity_id = change.entity_id
        entity = entities_by_id.get(entity_id, None)

        if not entity:
            entity = {
                'entity_id': entity_id,
                'entity_name': change.entity
            }
            entities_by_id[entity_id] = entity

        created_at = change.created_at
        created_at = created_at.replace(tzinfo=created_at.tzinfo or UTC).astimezone(UTC)
        changed_at = datetime.fromisoformat(str(entity['changed_at'])) if entity.get('changed_at') else None

        if changed_at is not None and changed_at >= created_at:
            logger.warning('Skipping change %s at or before the last applied timestamp', change.id)
            skipped += 1
            continue

        entity['change_id'] = str(change.id)
        entity['changed_at'] = str(created_at)

        entity['name'] = snapshot.get('name', '')
        entity['date'] = snapshot.get('date', '')
        entity['from'] = snapshot.get('from', '')
        entity['till'] = snapshot.get('till', '')
        entity['duration'] = snapshot.get('duration', '')

        logger.info(f'Change {change.id} has been applied to entity {entity_id}!')

        applied += 1

    return {
        'skipped': skipped,
        'applied': applied
    }
