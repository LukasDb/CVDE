from abc import ABC, abstractmethod
import multiprocessing as mp
import sys
from typing import Union

import cvde
from .run_logger import RunLogger


class Job(ABC):
    def __init__(
        self,
        *,
        run_name: str,
        config_name: str,
        tags: list[str] = [],
    ) -> None:
        self.name = self.__class__.__name__

        self.config = cvde.ws_tools.load_config(config_name)
        self.tracker = cvde.job.RunLogger.create(self.name, config_name, run_name=run_name)
        self.tracker.set_tags(tags)

    @abstractmethod
    def run(self) -> None:
        pass

    @abstractmethod
    def on_terminate(self) -> None:
        pass
