import logging
import os

from event_worker.streamelements.api import Channels
from event_worker.streamelements.socketclient import Websocket

logging.basicConfig(level=os.environ.get("SE_CLIENT_LOG_LEVEL", "WARNING"),
                    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s - (%(filename)s:%(lineno)d)',
                    datefmt='%Y-%m-%dT%H:%M:%S%z')

def main():
    guid = os.environ.get("SE_CLIENT_GUID", None)
    url = os.environ.get("SE_CLIENT_API_URL", "https://api.streamelements.com/kappa/v2")
    if guid is None:
        channels = Channels(url, os.environ.get("SE_CLIENT_JWT"))
        profile = channels.me()
        guid = profile.get("_id", None)

    if guid is None:
        raise ValueError("SE_CLIENT_GUID was not provided and could not "
                         "be retrieved from API")

    socket = Websocket(reconnection_attempts=5)
    socket.connect()
    socket.wait()


if __name__ == "__main__":
    main()
