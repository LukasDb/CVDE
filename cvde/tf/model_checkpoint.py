import tensorflow as tf
from cvde.job import job_tracker


class ModelCheckpoint(tf.keras.callbacks.ModelCheckpoint):
    def __init__(self, tracker: job_tracker.JobTracker, **kwargs):
        super().__init__(
            filepath=str(tracker.weights_root.resolve()) + "/checkpoints/", **kwargs
        )
