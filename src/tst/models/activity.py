from pydantic import BaseModel, ConfigDict, Field


class Activity(BaseModel):
    model_config = ConfigDict(validate_by_name=True, serialize_by_alias=True)

    id: str
    name: str
    date: str
    from_: str = Field(alias='from')
    till: str
    duration: str
    color: str | None = None
