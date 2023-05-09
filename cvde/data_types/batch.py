from .data_type import DataType


class Batch(DataType):
    """ represents a batch of data"""

    def __init__(self, batch_size: int, inner_spec, **kwargs) -> None:
        super().__init__(name='batch', **kwargs)
        self.batch_size = batch_size
        self.inner_spec = inner_spec
        
    def __str__(self):
        return f"<Batch [{self.batch_size}] {str(self.inner_spec)}>"