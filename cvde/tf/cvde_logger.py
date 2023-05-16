from cvde.job.job_tracker import JobTracker
from cvde.tf import Callback
from typing import Dict
import tensorflow as tf
import sys
import tensorflow as tf
import time


class CVDElogger(Callback):
    def __init__(self, tracker: JobTracker, *args, **kwargs):
        super().__init__(tracker, *args, **kwargs)
        self.last_time = time.perf_counter()
        self.epoch = 0

    def on_epoch_end(self, epoch: int, logs: Dict = None) -> None:
        self.epoch = epoch
        for k, v in logs.items():
            self.log_scalar(k, v)

    def on_train_batch_end(self, batch: int, logs: Dict = None) -> None:
        self.print_progress('Training', batch, logs)

    def on_val_batch_end(self, batch: int, logs: Dict = None) -> None:
        self.print_progress('Validation: ', batch, logs)

    def print_progress(self, prefix: str, batch: int, logs: Dict = None) -> None:
        t = time.perf_counter()
        dt = t - self.last_time
        self.last_time = t
        tf.print("Epoch: ", self.epoch, output_stream=sys.stdout)
        tf.print(f"{prefix} Batch: {batch} ({1/dt:.2f}B/sec): {logs}", output_stream=sys.stdout)