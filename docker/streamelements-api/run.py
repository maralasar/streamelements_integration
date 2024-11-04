import datetime as dt
import logging
import os
import time

from event_worker.streamelements import api
from event_worker.streamelements.apiclient import StreamelementsAPIIngester

CONFIG = "./config.yaml"

logging.basicConfig(level=os.environ.get("SE_API_LOG_LEVEL", "WARNING"),
                    format='%(asctime)s - %(levelname)s - %(name)s  - %(message)s - %(filename)s:%(lineno)d',
                    datefmt='%Y-%m-%dT%H:%M:%S%z')

_logger = logging.getLogger("main")


def main():
    _logger.debug("Requesting ChannelID")
    channel = api.Channels(
        api_url=os.environ.get("SE_API_URL", "https://api.streamelements.com/kappa/v2"),
        jwt=os.environ['SE_API_JWT']).me()
    guid = channel["_id"]
    _logger.info(f"JWT Token belongs to channel ID {guid}")

    date_start = os.environ.get("SE_API_DATE_START", dt.datetime.now(tz=dt.timezone.utc))
    if isinstance(date_start, str):
        date_start = dt.datetime.fromisoformat(date_start)

    after = date_start
    sleep_time = int(os.environ.get("SE_API_SLEEP", 5))
    throttle_time = int(os.environ.get("SE_API_THROTTLE", 5))
    with StreamelementsAPIIngester(guid=guid) as client:
        while True:
            data_last_iter = dt.datetime.now(tz=dt.timezone.utc)
            date_last_datapoint = client.retrieve_data(after) - dt.timedelta(seconds=1e-5)
            _logger.debug(f"Waiting {throttle_time} seconds before next iteration")
            time.sleep(throttle_time)

            if date_last_datapoint >= dt.datetime.now(tz=dt.timezone.utc):
                _logger.info("Last request window extended into the future. Choose SE_API_SLEEP larger than SE_API_REQUEST_WINDOW")
            after = min(date_last_datapoint, data_last_iter)

            if after >= data_last_iter - dt.timedelta(seconds=sleep_time):
                _logger.info(f"Last requested window ended at {after.isoformat()}. Waiting {sleep_time} seconds")
                time.sleep(sleep_time)


if __name__ == "__main__":
    main()
