from .data_type import DataType
import numpy as np


class Numerical(DataType):
    def __init__(self) -> None:
        """ Holds arbitrary numerical data (numpy, tensors, etc)"""
        super().__init__()
        