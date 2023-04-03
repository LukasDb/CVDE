from .data_type import DataType
import numpy as np


class Numerical(DataType):
    def __init__(self, **kwargs) -> None:
        """ Holds arbitrary numerical data (numpy, tensors, etc)"""
        super().__init__(**kwargs)
        