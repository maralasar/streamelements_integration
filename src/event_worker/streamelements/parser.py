import datetime as dt
import logging

from pydantic import BaseModel, field_serializer
from pydantic.v1 import PastDate

from event_worker.writer.models import WriterEvent, EventData, Parser

_logger = logging.getLogger(__name__)


class InputEvent(BaseModel):
    provider: str
    activityId: str
    nonce: str
    createdAt: dt.datetime
    updatedAt: dt.datetime
    sessionEventsCount: int
    data: dict
    activityGroup: str | None = None
    isMock: bool | None = False

    @field_serializer("createdAt", "updatedAt")
    def serialize_dt(self, date: dt.datetime, _info) -> str:
        return date.isoformat()

class APIParser(Parser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __call__(self, event_type: str, **event_data):
        writer_event = WriterEvent(
            source="streamelements-api",eventType=event_type,
            eventId=event_data["_id"],
            channel=event_data.get("channel", None),
            dataProvider=event_data.get("provider", None),
            createdAt=event_data.get("createdAt", None),
            updatedAt=event_data.get("updatedAt", None),
            data=EventData(**event_data["data"])
        )

        return writer_event

class SocketParser(Parser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __call__(self, event_type: str, **event_data):
        writer_event = WriterEvent(
            source="streamelements", eventType=event_type,
            eventId=event_data.get("activityId"),
            eventGroup=event_data.get("activityGroup", None),
            channel=event_data.get("channel", None),
            dataProvider=event_data.get("provider", None),
            createdAt=event_data.get("createdAt", None),
            updatedAt=event_data.get("updatedAt", None),
            eventCount=event_data.get("sessionEventsCount", None),
            isMock=event_data.get("isMock", False)
        )
        data = event_data.get("data", {})

        if not data:
            _logger.error(f"Something went wrong. The event had no real data: {event_data}")

        if event_type == "subscriber":
            writer_event.data = EventData(
                username=data.get("username", None),
                displayName=data.get("displayName", None),
                amount=data.get("amount", None),
                message=data.get("message", None),
                tier=data.get("tier", None),
                quantity=data.get("quantity", None),
                gifted=data.get("gifted", None),
                avatar=data.get("avatar", None),
                sender=data.get("sender", None),)

        elif event_type == "communityGiftPurchase":
            writer_event.data = EventData(
                username=data.get("username", None),
                displayName=data.get("displayName", None),
                amount=data.get("amount", None),
                message=data.get("message", None),
                tier=data.get("tier", None),
                quantity=data.get("quantity", None),
                sender=data.get("sender", None),
                avatar=data.get("avatar", None), )

        elif event_type == "follow":
            writer_event.data = EventData(
                username=data.get("username", None),
                displayName=data.get("displayName", None),
                quantity=data.get("quantity", None),
                avatar=data.get("avatar", None), )

        elif event_type == "cheer":
            writer_event.data = EventData(
                username=data.get("username", None),
                displayName=data.get("displayName", None),
                amount=data.get("amount", None),
                message=data.get("message", None),
                tier=data.get("tier", None),
                quantity=data.get("quantity", None),
                avatar=data.get("avatar", None), )

        elif event_type == "tip":
            writer_event.data = EventData(
                username=data.get("username", None),
                displayName=data.get("displayName", None),
                amount=data.get("amount", None),
                message=data.get("message", None),
                quantity=data.get("quantity", None),
                currency=data.get("currency", None),
                avatar=data.get("avatar", None), )

        elif event_type == "raid":
            writer_event.data = EventData(
                username=data.get("username", None),
                displayName=data.get("displayName", None),
                amount=data.get("amount", None),
                message=data.get("message", None),
                tier=data.get("tier", None),
                quantity=data.get("quantity", None),
                avatar=data.get("avatar", None), )

        else:
            _logger.warning(f"event_type {event_type} not supported")

        _logger.info(f"Parsed: {writer_event}")
        return writer_event