from abc import ABC, abstractmethod
import sys
from typing import Any

from .run_logger import RunLogger


class Job(ABC):
    def __init__(self, *, run_name: str, config: dict[str, Any], tags: list[str] = []) -> None:
        self.name = self.__class__.__name__
        self.config = config
        self.logger = RunLogger.create(self.name, config, run_name=run_name)
        self.logger.set_tags(tags)

    @property
    def tracker(self) -> RunLogger:
        print("WARNING: job.tracker is deprecated. Use job.logger instead.", file=sys.stderr)
        return self.logger

    @abstractmethod
    def run(self) -> None:
        pass

    @abstractmethod
    def on_terminate(self) -> None:
        pass
