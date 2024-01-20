from abc import ABC, abstractmethod
import multiprocessing as mp
import sys
from typing import Union

import cvde
from .job_tracker import JobTracker


class Job(ABC):
    def __init__(
        self,
        *,
        run_name: Union[str, None] = None,
        config_name: Union[str, None] = None,
        folder_name: Union[str, None] = None,
        tags: list[str] = [],
    ) -> None:
        self.name = self.__class__.__name__
        if folder_name is not None and config_name is None:
            self.tracker = cvde.job.JobTracker.from_log(folder_name)
            self.config = self.tracker.config
            self.name = self.tracker.name

        elif folder_name is None and config_name is not None and run_name is not None:
            self.config = cvde.ws_tools.load_config(config_name)
            self.tracker = cvde.job.JobTracker.create(self.name, config_name, run_name=run_name)
            self.tracker.set_tags(tags)
            
        self.tracker.set_thread_ident()


    @abstractmethod
    def run(self) -> None:
        pass
