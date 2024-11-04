import json
import logging
import os
from typing import Any

import paho.mqtt.client as mqtt
from yaml import Loader, load

from event_worker.util import factory
from event_worker.writer.models import Writer

_logger = logging.getLogger(__name__)


class Dispatcher(mqtt.Client):
    def __init__(self, config_path: str = "./config.yaml"):
        super().__init__(protocol=mqtt.MQTTv5)
        with open(config_path, "r") as f:
            self.config: dict = load(f, Loader=Loader)

        self.logger = logging.getLogger(__name__ + '.Dispatcher')

        self.username_pw_set(username=os.environ.get('DIGESTER_MQTT_USER'),
                             password=os.environ.get('DIGESTER_MQTT_PASSWD'))

        self.parser = {}
        for source, cfg in self.config.get("ingests").items():
            _name = cfg.pop("parser")
            self.parser[source] = factory(module_class_string=_name,
                                          super_cls=None, **cfg)

        self.writer: dict[str, Writer] = {}
        for writer, cfg in self.config.get("writers").items():
            _name = cfg.pop("class")
            self.writer[writer] = factory(module_class_string=_name,
                                          super_cls=Writer, **cfg)

        self.on_message = on_message
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.on_connect_fail = on_connect_fail
    def __enter__(self):
        self.connect(host=os.environ.get('DIGESTER_MQTT_HOST'),
                     port=int(os.environ.get('DIGESTER_MQTT_PORT', 1883)))
        for writer in self.writer.values():
            writer.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for writer in self.writer.values():
            writer.close()
        self.loop_stop()
        self.disconnect()



def on_connect(client: Dispatcher, userdata: Any, flags,
               rc: mqtt.ReasonCode, properties: mqtt.Properties = None):
    client.logger.info("Connected to MQTT")
    # subscribe to all mqtt topics
    for source, cfg in client.config.get("ingests").items():
        client.subscribe(f"/{source}/#")
        client.logger.info(f"Subscribed to /{source}/#")


def on_disconnect(client: Dispatcher, userdata: Any,
                  rc: mqtt.ReasonCode = None,
                  properties: mqtt.Properties = None):
    client.logger.info(f"Disconnected from MQTT with reason {rc}")


def on_connect_fail(client: Dispatcher, userdata: Any):
    client.logger.error("Could not connect to MQTT")


def on_message(client: Dispatcher, userdata, msg: mqtt.MQTTMessage):
    topic = msg.topic
    _, source, *_, event_type = topic.split("/")
    try:
        _logger.debug(f"Decoding message: {msg.payload}")
        payload = json.loads(msg.payload)
    except json.JSONDecodeError as err:
        _logger.error(f"Could not decode message: {err}")
        return

    if source in client.parser:
        parsed_event = client.parser[source](event_type=event_type, **payload)
    else:
        client.logger.error(f"No parser defined for ingest from {source}")
        raise ValueError(f"No parser defined for ingest from {source}")

    # TODO (maralasar): Check if the write events should be called in an
    #  extra thread ALL THE TIME or if it is enough if the writer itself
    #  handles this
    for name, writer in client.writer.items():
        writer.write(event=parsed_event)

    pass
