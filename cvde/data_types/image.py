import streamlit as st
from .data_type import DataType
import numpy as np


class Image(DataType):
    def __init__(self, shape: tuple, format: str, decode=None) -> None:
        """ Specify Image Datatype. Specify format (CHW, HWC..) to mark height,
        width and channel dimension. Optionally provide a decode function to 
        retrieve a visualization of the image.
        If the decode function changes the shape, modify shape and format accordingly"""
        self.shape = shape
        self.format = format.lower()
        self.decode = decode
        super().__init__()

    def get_visualization(self, data) -> np.ndarray:
        if hasattr(data, 'numpy'):
            data = data.numpy()

        if self.decode is not None:
            data = self.decode(data)

        h_ind = self.format.index('h')
        w_ind = self.format.index('w')

        try:
            c_ind = self.format.index('c')
            data = np.transpose(data, [h_ind, w_ind, c_ind])

        except ValueError:
            data = np.transpose(data, [h_ind, w_ind])
            data = np.expand_dims(data, -1)

        return data
        