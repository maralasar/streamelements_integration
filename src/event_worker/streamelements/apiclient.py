import datetime as dt
import json
import logging
import os

from paho.mqtt import client as mqtt

from event_worker.streamelements import api
from event_worker.streamelements.meta import ActivityKinds

_logger = logging.getLogger(__name__)


class StreamelementsAPIIngester:
    def __init__(self, guid: str):
        # check for a persistent_file_storage
        self.guid = guid

        date_start = os.environ.get("SE_API_DATE_START", dt.datetime.now(tz=dt.timezone.utc))
        if date_start is None:
            date_start = dt.datetime.now(tz=dt.timezone.utc)
        if isinstance(date_start, str):
            date_start = dt.datetime.fromisoformat(date_start)
        self.date_start = date_start

        self.__prev_ids = []

        self.api_client = api.Activities(
            api_url=os.environ.get("SE_API_URL", "https://api.streamelements.com/kappa/v2"),
            guid=guid, jwt=os.environ.get("SE_API_JWT"))
        self.mqtt_client = mqtt.Client(protocol=5)
        self.mqtt_client.enable_logger()
        self.first_connect = True

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def open(self):
        self.mqtt_client.username_pw_set(username=os.environ.get('SE_API_MQTT_USER'),
                                         password=os.environ.get('SE_API_MQTT_PASSWD'))
        self.mqtt_client.connect(
            host=os.environ.get('SE_API_MQTT_HOST'),
            port=int(os.environ.get('SE_API_MQTT_PORT', 1883))
        )
        self.mqtt_client.loop_start()

    def close(self):
        _logger.info("Writing already requested events to file")
        self.mqtt_client.loop_stop()

    def retrieve_data(self, date_start):
        date_end = date_start + dt.timedelta(seconds=int(os.environ.get("SE_API_REQUEST_WINDOW", 600)))

        res = self.api_client.channel(
            after=date_start, before=date_end, limit=500,
            types=[ActivityKinds.TIP, ActivityKinds.SUBSCRIBER, ActivityKinds.CHEER])

        last_data = date_start
        for event in res:
            topic = f"/streamelements-api/event/{event['type']}"
            _logger.debug(f"sending {event} to MQTT {topic}")
            self.mqtt_client.publish(topic=topic, payload=json.dumps(event))
            date = dt.datetime.fromisoformat(event["createdAt"])
            if date > date_end:
                last_data = date
        _logger.info(f"Retrieved {len(res)} events between "
                     f"{date_start.isoformat()} and {date_end.isoformat()}")
        # if there were too many events, the next call should start according to that date
        if len(res) >= 500:
            _logger.warning(f"There were more than 500 events between "
                            f"{date_start.isoformat()} and {date_end.isoformat()}")
            date_end = last_data
        return date_end
