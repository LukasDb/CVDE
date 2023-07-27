from abc import ABC, abstractmethod
from .job_tracker import JobTracker
import cvde.workspace_tools as ws_tools
from cvde.workspace import Workspace as WS
import threading
from typing import Union


class JobTerminatedException(Exception):
    pass


class Job(ABC):
    def __init__(
        self, *, config_name: Union[str, None] = None, folder_name: Union[str, None] = None
    ):
        self.name = self.__class__.__name__

        if folder_name is not None and config_name is None:
            self.tracker = JobTracker.from_log(folder_name)
            self.config = self.tracker.config
        elif folder_name is None and config_name is not None:
            self.config = ws_tools.load_config(config_name)
            self.tracker = JobTracker.create(self.name, config_name)

        self._stop_queue = WS()._stop_queue

    @staticmethod
    def load_job(__job_name) -> type["Job"]:
        return ws_tools.load_module("jobs", __job_name)

    def stop(self):
        print("Job stopped: ", self.name)
        self._stop_queue.put(self.tracker.ident)

    @property
    def is_stopped(self):
        with self._stop_queue.mutex:
            return self.tracker.ident in self._stop_queue.queue
            

    def launch(self):
        """non-blocking launch job"""
        job_thread = threading.Thread(
            target=self._run, name="thread_" + self.tracker.unique_name
        )
        job_thread.start()

    def _run(self):
        self.tracker.set_thread_ident()

        class Unbuffered:
            def __init__(self, stream, file):
                self.stream = stream
                self.fp = open(file, "w")

            def write(self, data):
                self.stream.write(data)
                self.stream.flush()
                self.fp.write(data)
                self.fp.flush()

            def flush(self):
                self.fp.flush()
                self.stream.flush()

        import sys

        sys.stdout = Unbuffered(sys.stdout, self.tracker.stdout_file)
        sys.stderr = Unbuffered(sys.stderr, self.tracker.stderr_file)

        # reload potentially changed modules
        WS().reload_modules()

        self.run()

        print("Job finished: ", self.name)

    @abstractmethod
    def run(self):
        pass
