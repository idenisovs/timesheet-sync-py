import csv
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Lock

from fastapi import APIRouter

from .models.change import Change

sync_api = APIRouter()
changes_path = Path('changes.tsv')
changes_lock = Lock()


def _with_utc_default(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def _read_changes() -> dict[str, datetime]:
    with changes_path.open(encoding='utf-8', newline='') as file:
        return {
            row['id']: _with_utc_default(datetime.fromisoformat(row['datetime']))
            for row in csv.DictReader(file, delimiter='\t')
        }


def _write_changes(registered_changes: dict[str, datetime]) -> None:
    with TemporaryDirectory(dir=changes_path.parent) as directory:
        temporary_path = Path(directory) / changes_path.name
        with temporary_path.open('w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file, delimiter='\t', lineterminator='\n')
            writer.writerow(('id', 'datetime'))
            writer.writerows(
                (change_id, created_at.isoformat())
                for change_id, created_at in registered_changes.items()
            )
        temporary_path.replace(changes_path)


@sync_api.post('/sync')
def sync(changes: list[Change]) -> dict[str, str]:
    with changes_lock:
        needs_write = False
        try:
            registered_changes = _read_changes()
        except FileNotFoundError:
            registered_changes = {}
            needs_write = True

        for change in changes:
            change_id = str(change.id)
            created_at = _with_utc_default(change.created_at)
            registered_at = registered_changes.get(change_id)
            if registered_at is None or registered_at < created_at:
                registered_changes[change_id] = created_at
                needs_write = True

        if needs_write:
            _write_changes(registered_changes)

    return {'message': 'ok'}
