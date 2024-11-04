import json
import logging
import os

import socketio
import paho.mqtt.client as mqtt


class Websocket(socketio.Client):
    def __init__(self, *args, **kwargs):
        kwargs.update({"logger": logging.getLogger(__name__ + ".socketio"),
                       "engineio_logger": logging.getLogger(__name__ + ".engineio")
                       })
        kwargs["engineio_logger"].setLevel(logging.WARNING)
        super().__init__(*args, **kwargs)

        self.mqtt_client = mqtt.Client(protocol=5)
        self.mqtt_client.enable_logger(logging.getLogger(__name__ + ".mqtt"))
        self.first_connect = True

    def connect(self, *args, **kwargs):
        self.mqtt_client.username_pw_set(username=os.environ.get('SE_CLIENT_MQTT_USER'),
                                         password=os.environ.get('SE_CLIENT_MQTT_PASSWD'))
        self.mqtt_client.connect(
            host=os.environ.get('SE_CLIENT_MQTT_HOST'),
            port=int(os.environ.get('SE_CLIENT_MQTT_PORT', 1883))
        )
        self.mqtt_client.loop_start()

        self.on("connect", self.handle_connect)
        self.on("disconnect", self.handle_disconnect)
        self.on("authenticated", self.handle_auth)
        self.on("unauthorized", self.handle_unauth)
        self.on('event:test', self.handle_event_test)
        self.on('event', self.handle_event)
        self.on('event:update', self.handle_event_update)
        self.on('event:reset', self.handle_event_reset)
        self.on('*', self.handle_catch_all)

        super().connect(os.environ.get("SE_CLIENT_SOCKET_URL",
                                       "https://realtime.streamelements.com"),
                        transports=['websocket'])
        return self

    # ------------------------------------------------------------------
    # Anything below is just for callbacks of different events from the
    # SocketIO library
    # ------------------------------------------------------------------
    def handle_connect(self):
        self.logger.info('Successfully connected to the websocket')
        self.emit('authenticate', {'method': 'jwt', 'token': os.environ.get('SE_CLIENT_JWT')})

    def handle_disconnect(self):
        self.logger.info('Disconnected from websocket')

    def handle_auth(self, data):
        channel_id = data.get('channelId')
        self.logger.info(f'Successfully connected to channel {channel_id}')
        self.first_connect = False
        if not self.first_connect:
            self.logger.warning("This was not the first time connecting "
                                "during the current runtime")

    def handle_unauth(self, data):
        self.logger.info(f'Unauthorized: {data}')

    def handle_event_test(self, *data):
        self.logger.debug(f'Event test: {data}')

    def handle_event(self, *data):
        self.logger.int(f'Event: {data}')
        content, info = data
        event_type = content.get('type')
        topic = f"/streamelements-socket/event/{event_type}"
        # self.logger.debug(f"sending {content} to MQTT {topic}")
        self.mqtt_client.publish(topic, payload=json.dumps(content))

    def handle_event_update(self, *data):
        self.logger.debug(f'Session update: {data}')

    def handle_event_reset(self, *data):
        self.logger.debug(f'Session reset: {data}')

    def handle_catch_all(self, *data):
        self.logger.debug(f'Received an uncaught event: {data}')
