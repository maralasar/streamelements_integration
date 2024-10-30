import logging
import os

from event_worker import Dispatcher

URL = "https://api.streamelements.com/kappa/v2"

logging.basicConfig(level=os.environ.get("DIGESTER_LOG_LEVEL", "WARNING"),
                    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s - (%(filename)s:%(lineno)d)',
                    datefmt='%Y-%m-%dT%H:%M:%S%z')


def main():
    with Dispatcher(config_path=os.environ.get("DIGESTER_CFG_PATH", "config.yaml")) as dispatcher:
        dispatcher.loop_forever()


if __name__ == "__main__":
    main()
