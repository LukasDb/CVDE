import numpy as np
from abc import ABC, abstractmethod

class DataType(ABC):
    pass


"""
IMAGES:
    1 or 3, 4 channels, HWC/CHW, float/uint8

Numerical:
    labels, vectors

Keypoints2D:
    [n,2] array

Keypoints3D:
    [n, 3] array

BBOX:
    [4,] array, x1y1x2y2, xywh
""" 