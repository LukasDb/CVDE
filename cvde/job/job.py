from abc import ABC, abstractmethod
import threading
import sys
from typing import Union

import cvde


class Job(ABC):
    def __init__(
        self,
        *,
        run_name: Union[str, None] = None,
        config_name: Union[str, None] = None,
        folder_name: Union[str, None] = None,
        tags: list[str] = []
    ):
        self.name = self.__class__.__name__
        if folder_name is not None and config_name is None:
            self.tracker = cvde.job.JobTracker.from_log(folder_name)
            self.config = self.tracker.config
            self.name = self.tracker.name

        elif folder_name is None and config_name is not None and run_name is not None:
            self.config = cvde.ws_tools.load_config(config_name)
            self.tracker = cvde.job.JobTracker.create(self.name, config_name, run_name=run_name)
            self.tracker.set_tags(tags)

        self._stop_queue = cvde.WS().stop_queue

    @staticmethod
    def load_job(__job_name) -> type["Job"]:
        return cvde.ws_tools.load_module("jobs", __job_name)

    def stop(self):
        self._stop_queue.add(self.tracker.ident)

    def is_stopped(self):
        if self.tracker.ident in self._stop_queue:
            self._stop_queue.remove(self.tracker.ident)
            return True
        else:
            return False

    def launch(self):
        """non-blocking launch job"""
        job_thread = threading.Thread(target=self._run, name="thread_" + self.tracker.unique_name)
        job_thread.start()

    def _run(self):
        """runs in thread"""
        self.tracker.set_thread_ident()
        assert isinstance(sys.stdout, cvde.ThreadPrinter)
        assert isinstance(sys.stderr, cvde.ThreadPrinter)

        sys.stdout.register_new_out(self.tracker.stdout_file)
        sys.stderr.register_new_out(self.tracker.stderr_file)
        self.run()
        cvde.gui.notify("Job finished: ", self.name)

    @abstractmethod
    def run(self):
        pass
