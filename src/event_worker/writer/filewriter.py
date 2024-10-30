import json
import logging
from pathlib import Path

from event_worker.writer.models import Writer, WriterEvent


class FileWriter(Writer):
    def __init__(self, filepath: str | Path = "./output/FileWriter.jsonl",
                 create: bool = True, encoding="utf-8"):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.filepath = filepath
        self.encoding = encoding

        if not isinstance(filepath, Path):
            self.filepath = Path(self.filepath)

        if not self.filepath.exists() and not create:
            raise FileNotFoundError("File does not exist. Define create=True or create it yourself.")

        if not self.filepath.exists():
            with open(self.filepath, "w+", encoding=self.encoding) as f:
                self.logger.info(f"File {self.filepath} does not exist. Creating it.")

        if not self.filepath.is_file():
            raise FileNotFoundError("Path is not a file.")

        if not self.filepath.suffix == ".jsonl":
            raise ValueError("File must be of type '*.jsonl'")

        self.file = None

    def open(self) -> "FileWriter":
        self.logger.info(f"Opening file {self.filepath}")
        self.file = open(self.filepath, "a+", encoding=self.encoding)
        return self

    def close(self) -> None:
        self.logger.info(f"Closing file {self.filepath}")
        self.file.close()

    def health_check(self) -> None:
        pass

    def write(self, event: WriterEvent) -> None:
        self.logger.info(f"Writing event to file: {event}")
        json.dump(event.model_dump(exclude_none=True), self.file)
        self.file.write("\n")
