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
            last_iteration = dt.datetime.now(tz=dt.timezone.utc)
            last_date = client.retrieve_data(after) - dt.timedelta(seconds=1e-5)
            _logger.debug(f"Waiting {throttle_time} seconds before next iteration")
            time.sleep(throttle_time)
            after = last_date
            if last_date >= last_iteration - dt.timedelta(seconds=sleep_time):
                _logger.info(f"Last requested window ended at {after.isoformat()}. Waiting {sleep_time} seconds")
                time.sleep(sleep_time)


if __name__ == "__main__":
    main()
