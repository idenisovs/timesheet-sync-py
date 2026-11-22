from datetime import UTC, datetime

from fastapi import APIRouter, Request

healthcheck_api = APIRouter()


@healthcheck_api.get('/healthcheck')
def healthcheck(request: Request) -> dict[str, str]:
    return {
        'service': 'timesheet-sync',
        'status': 'OK',
        'version': request.app.version,
        'timestamp': datetime.now(UTC).isoformat(timespec='milliseconds').replace('+00:00', 'Z'),
    }
