from datetime import datetime
from typing import Literal

from pydantic import UUID7, BaseModel, Field, StrictInt


class Change(BaseModel):
    id: UUID7
    entity: Literal['activity', 'issue', 'project']
    entity_id: str | StrictInt = Field(alias='entityId')
    before: dict[str, object] | None
    after: dict[str, object] | None
    status: str
    created_at: datetime = Field(alias='createdAt')
