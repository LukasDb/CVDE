import numpy as np
import tensorflow as tf

from cvde.job.job_tracker import JobTracker


class Callback(tf.keras.callbacks.Callback):
    """Wrapper arount tf.keras.callbacks.Callback to provide logging functionaly for CVDE"""

    def __init__(self, tracker: JobTracker, *args, **kwargs):
        self.tracker = tracker

    def log_scalar(self, name, scalar):
        self.tracker.log(name, scalar)

    def log_image(self, name, image):
        self.tracker.log(name, image)
