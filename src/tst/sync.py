import csv
import logging
from datetime import UTC, datetime
from threading import Lock

from fastapi import APIRouter

from .models.activity import Activity
from .models.change import Change

logger = logging.getLogger(__name__)

ENTITY_FIELDS = (
    'entity_id',
    'entity_name',
    'name',
    'date',
    'from',
    'till',
    'duration',
    'change_id',
    'changed_at',
    'removed_at',
)

sync_api = APIRouter()
sync_lock = Lock()


def _to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)

    return value.astimezone(UTC)


@sync_api.post('/sync')
def sync(changes: list[Change]) -> dict[str, str]:
    logger.info('SYNC endpoint received %d changes', len(changes))

    with sync_lock, open('entities.tsv', 'r+', encoding='utf-8', newline='') as entities:
        reader = csv.DictReader(entities, delimiter='\t')
        rows = list(reader)

        for change in changes:
            if change.entity != 'activity':
                logger.warning(f'Skipping the entity {change.entity}!')
                continue

            entity_id = str(change.entity_id)
            row = next((row for row in rows if row['entity_id'] == entity_id), None)

            change_created_at = _to_utc(change.created_at)

            if row is None:
                logger.info('Creating a new entity row!')

                row = {
                    'entity_id': entity_id,
                    'entity_name': change.entity,
                    'removed_at': None,
                }

                rows.append(row)
            else:
                row_changed_at = _to_utc(datetime.fromisoformat(row['changed_at']))

                if row_changed_at > change_created_at:
                    logger.info('There is a more recent change, skipping!')
                    continue

            row['change_id'] = str(change.id)
            row['changed_at'] = change_created_at.isoformat()

            if change.after:
                logger.info(f'Updating the {change.entity}!')
                activity = Activity.model_construct(**change.after)

                row['name'] = activity.name
                row['date'] = activity.date
                row['from'] = activity.from_
                row['till'] = activity.till
                row['duration'] = activity.duration
                row['removed_at'] = None
            else:
                logger.info(f'Marking the {change.entity} as removed!')
                row['removed_at'] = change_created_at.isoformat()

            logger.info('Writing the changes back to the TSV!')
            writer = csv.DictWriter(entities, ENTITY_FIELDS, delimiter='\t', lineterminator='\n')
            entities.seek(0)
            writer.writeheader()
            writer.writerows(rows)
            entities.truncate()

        return {'message': 'ok'}
