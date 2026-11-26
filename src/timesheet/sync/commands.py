import logging
from datetime import UTC, datetime

from timesheet.models.activity import Activity
from timesheet.models.change import Change

logger = logging.getLogger(__name__)

entities_by_id = {}


def apply_changes(changes: list[Change]) -> dict[str, int]:
    logger.debug('Applying changes!')

    skipped = 0
    applied = 0

    for change in changes:
        if change.entity != 'activity':
            logger.warning(f'Skipping {change.entity}!')
            skipped += 1
            continue

        if not change.after and not change.before:
            logger.warning(f'Change {change.id} is missing both snapshots!')
            skipped += 1
            continue

        entity_id = change.entity_id

        change_created_at = change.created_at
        change_created_at = change_created_at.replace(tzinfo=change_created_at.tzinfo or UTC).astimezone(UTC)

        entity = entities_by_id.get(entity_id)

        if entity is not None and datetime.fromisoformat(entity['changed_at']) >= change_created_at:
            logger.warning('Skipping change %s at or before the last applied timestamp', change.id)
            skipped += 1
            continue

        snapshot = change.after if change.after is not None else change.before
        activity = Activity.model_validate(snapshot)

        entities_by_id[entity_id] = {
            'entity_id': entity_id,
            'entity_name': change.entity,
            **activity.model_dump(exclude={'id'}, exclude_none=True),
            'change_id': str(change.id),
            'changed_at': str(change_created_at),
            'removed_at': str(change_created_at) if change.after is None else None
        }

        logger.info(f'Change {change.id} has been applied to entity {entity_id}!')

        applied += 1

    logger.info(f'Applied {applied} changes, skipped {skipped} changes!')

    return {
        'skipped': skipped,
        'applied': applied
    }


def sync(changes: list[Change]) -> dict[str, int]:
    return apply_changes(changes)
