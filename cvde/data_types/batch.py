from .data_type import DataType

class Batch(DataType):
    """ represents a batch of data"""
    def __init__(self, batch_size: int, inner_spec) -> None:
        self.batch_size = batch_size
        self.inner_spec = inner_spec