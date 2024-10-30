import abc
import datetime as dt
from pydantic import BaseModel, field_serializer, AnyHttpUrl

from typing import Any


class EventData(BaseModel):
    amount: int | None = None
    avatar: AnyHttpUrl | str | None = None
    displayName: str | None = None
    username: str | None = None
    message: str | None = None
    sender: str | None = None
    tier: Any | int | None = None
    quantity: int | None = None
    gifted: bool | None = False
    currency: str | None = None
    streak: int | None = None


class WriterEvent(BaseModel):
    source: str
    eventId: str
    eventType: str
    eventGroup: str | None = None
    channel: str | None = None
    dataProvider: str | None = None
    createdAt: dt.datetime | None = None
    updatedAt: dt.datetime | None = None
    data: EventData | None = None
    eventCount: int | None = None
    isMock: bool | None = False

    @field_serializer("createdAt", "updatedAt")
    def serialize_dt(self, date: dt.datetime, _info) -> str:
        return date.isoformat()


class Writer(abc.ABC):
    def __init__(self, *args, **kwargs) -> None:
        ...

    @abc.abstractmethod
    def write(self, event: WriterEvent) -> None:
        ...

    @abc.abstractmethod
    def close(self) -> None:
        ...

    @abc.abstractmethod
    def open(self) -> "Writer":
        ...

    @abc.abstractmethod
    def health_check(self) -> None:
        ...

    def __enter__(self):
        return self.open()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

class Parser(abc.ABC):
    def __init__(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    def __call__(self, event_type: str, **data) -> Writer:
        ...
