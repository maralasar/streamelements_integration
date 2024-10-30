import logging
import os

from .models import Writer, WriterEvent
import pymongo

_logger = logging.getLogger(__name__)

class DBWriter(Writer):
    def __init__(self, host: str,  user: str, password: str, port: int = 27071,):
        super().__init__()

        uri = os.environ.get('DIGESTER_MONGO_URI', None)
        if uri is None:
            uri = (f"mongodb://{user}:{password}@{host}:{port}")

        self.__uri = uri
        self.client: pymongo.MongoClient = None

    def write(self, event: WriterEvent) -> None:
        db = self.client[event.source]
        collections = db.list_collection_names()

        if event.eventType not in collections:
            collection = db.create_collection(event.eventType)
        else:
            collection = db.get_collection(event.eventType)

        res = collection.insert_one(event.model_dump())
        _logger.info(f"Inserted into mongoDB: {res}")

    def close(self) -> None:
        self.client.close()

    def open(self) -> None:
        self.client = pymongo.MongoClient(self.__uri, heartbeatFrequencyMS=30e3)

    def health_check(self) -> None:
        ...
