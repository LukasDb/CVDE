import numpy as np
from abc import ABC, abstractmethod

class DataType:
    name=None
    def __init__(self, name: str):
        self.name = name
        super().__init__()

"""
TODO
Keypoints2D:
    [n,2] array

Keypoints3D:
    [n, 3] array
"""