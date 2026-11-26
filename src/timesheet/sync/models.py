from datetime import datetime
from typing import Literal

from pydantic import UUID7, BaseModel, ConfigDict, Field, StrictInt


class Activity(BaseModel):
    model_config = ConfigDict(validate_by_name=True, serialize_by_alias=True)

    id: str
    name: str
    date: str
    from_: str = Field(alias='from')
    till: str
    duration: str
    color: str | None = None


class Change(BaseModel):
    id: UUID7
    entity: Literal['activity', 'issue', 'project']
    entity_id: str | StrictInt = Field(alias='entityId')
    before: dict[str, str] | None
    after: dict[str, str] | None
    status: str
    created_at: datetime = Field(alias='createdAt')
