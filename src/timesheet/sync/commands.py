from dataclasses import dataclass, field
import logging
from datetime import UTC, datetime

from timesheet.sync.models import Activity, Change

logger = logging.getLogger(__name__)

entities_by_id = {}


@dataclass
class ApplyChangesResult:
	applied: list[Change] = field(default_factory=list)
	skipped: list[Change] = field(default_factory=list)


def apply_changes(changes: list[Change]) -> ApplyChangesResult:
	logger.debug('Applying changes!')

	result = ApplyChangesResult()

	for change in changes:
		if change.entity != 'activity':
			logger.warning(f'Skipping {change.entity}!')
			result.skipped.append(change)
			continue

		if not change.after and not change.before:
			logger.warning(f'Change {change.id} is missing both snapshots!')
			result.skipped.append(change)
			continue

		entity_id = change.entity_id

		change_created_at = change.created_at
		change_created_at = change_created_at.replace(tzinfo=change_created_at.tzinfo or UTC).astimezone(UTC)

		entity = entities_by_id.get(entity_id)

		if entity is not None and datetime.fromisoformat(entity['changed_at']) >= change_created_at:
			logger.warning('Skipping change %s at or before the last applied timestamp', change.id)
			result.skipped.append(change)
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

		result.applied.append(change)

	logger.info(f'Applied {len(result.applied)} changes, skipped {len(result.skipped)} changes!')

	return result


def update_affected_days(changes):
	logger.debug('Updating affected days!')

	for change in changes:
		snapshot = change.after if change.after is not None else change.before
		activity = Activity.model_validate(snapshot)
		logger.debug(activity.date)


def sync(changes: list[Change]) -> dict[str, int]:
	result = apply_changes(changes)

	update_affected_days(result.applied)

	return {
		'applied': len(result.applied),
		'skipped': len(result.skipped)
	}
