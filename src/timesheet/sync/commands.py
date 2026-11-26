from dataclasses import dataclass, field
import logging
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path

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


def prepare_reports_dir() -> Path:
	reports_dir = Path(__file__).resolve().parents[3] / 'reports'
	reports_dir.mkdir(exist_ok=True)
	return reports_dir


def prepare_report_file(activity_date: str) -> str:
	year, week, _ = date.fromisoformat(activity_date).isocalendar()
	report_file_name = f'{year:04d}-{week:02d}.txt'
	(reports_dir / report_file_name).touch()
	return report_file_name


def get_changed_dates(changes):
	changed_dates: set[str] = set()

	for change in changes:
		snapshot = change.after if change.after is not None else change.before
		activity = Activity.model_validate(snapshot)
		changed_dates.add(activity.date)

	return changed_dates


def get_changed_weeks(changed_dates: set[str]):
	changed_weeks = {}

	for cd in changed_dates:
		logger.debug(f'Processing change date {cd}')

		year, week, _ = date.fromisoformat(cd).isocalendar()
		week_key = f'{year:04d}_{week:02d}'

		if week_key in changed_weeks:
			continue

		changed_weeks[week_key] = {}

		week_start = date.fromisocalendar(year, week, 1)

		for offset in range(7):
			day = (week_start + timedelta(days=offset)).isoformat()
			entities = [entity for entity in entities_by_id.values() if entity['date'] == day]
			changed_weeks[week_key][day] = entities

	return changed_weeks


def format_report_day(day: str, entities: list[dict]) -> str:
	minutes_by_group: dict[str, int] = {}

	for entity in entities:
		group = entity['name'].split(':', 1)[0].strip()
		start = time.fromisoformat(entity['from'])
		end = time.fromisoformat(entity['till'])
		start_minutes = start.hour * 60 + start.minute
		end_minutes = end.hour * 60 + end.minute
		duration = (end_minutes - start_minutes) % (24 * 60)
		minutes_by_group[group] = minutes_by_group.get(group, 0) + duration

	lines = [day, '-' * len(day)]

	for group, total_minutes in minutes_by_group.items():
		hours, minutes = divmod(total_minutes, 60)
		lines.append(f'{group} - {hours}h {minutes}m')

	return '\n'.join(lines)


def update_affected_weeks(changes):
	logger.debug('Updating affected days!')

	changed_dates = get_changed_dates(changes)

	logger.debug(f'The dates of changes: {changed_dates}')

	changed_weeks = get_changed_weeks(changed_dates)

	reports_dir = prepare_reports_dir()

	for week_key, days in changed_weeks.items():
		sections = [format_report_day(day, entities) for day, entities in days.items() if entities]
		content = '\n\n'.join(sections) + '\n' if sections else ''
		(reports_dir / f'{week_key}.txt').write_text(content, encoding='utf-8')

	# report_file_name = prepare_report_file(activity.date)
	return changed_weeks


def sync(changes: list[Change]) -> dict[str, int]:
	result = apply_changes(changes)

	update_affected_weeks(result.applied)

	return {
		'applied': len(result.applied),
		'skipped': len(result.skipped)
	}
