import tensorflow as tf


class ModelCheckpoint(tf.keras.callbacks.ModelCheckpoint):
    def __init__(self, tracker, **kwargs):
        super().__init__(self, filepath=str(tracker.weigts_root.resolve()), **kwargs)
