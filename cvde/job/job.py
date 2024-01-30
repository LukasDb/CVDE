from abc import ABC, abstractmethod
import sys
from typing import Any
from .run_logger import RunLogger


class Job(ABC):
    def __init__(self, *, logger: RunLogger, config: dict[str, Any]) -> None:
        self.name = self.__class__.__name__
        self.config = config
        self.logger = logger

    @property
    def tracker(self) -> RunLogger:
        print("WARNING: job.tracker is deprecated. Use job.logger instead.", file=sys.stderr)
        return self.logger

    @abstractmethod
    def run(self) -> None:
        pass

    def on_terminate(self) -> None:
        pass

    def is_stopped(self) -> bool:
        print(
            "WARNING: job.is_stopped() is deprecated. Please remove it from your code.",
            file=sys.stderr,
        )
        return False
