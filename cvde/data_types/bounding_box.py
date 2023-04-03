import cv2
from .data_type import DataType
from collections.abc import Mapping
import numpy as np
from typing import Dict
from plotbbox import plotBBox


class Bbox(DataType):
    def __init__(self, format: str = 'x1,y1,x2,y2,cls', relative: bool = False, labelmap: Dict[int, str] = None, colormap: Mapping = None, **kwargs) -> None:
        """ Specifies a bounding box.

        Parameters:
            format (str): Define bounding box format. Examples:
                            (min_x, min_y, max_x, max_y) == 'x1,y1,x2,y2'
                            [(center_x, center_y, width, height)] as '[x,y,w,h]'
            relative (bool): If bounding box is normalized to image dimensions [0, 1]
            colormap: Can used to map 'cls' to a BGR color
            labelmap: Can be used to map 'cls' to a readable string

        """
        super().__init__(**kwargs)
        self.relative = relative

        self.is_list = format.startswith('[') and format.endswith(']')
        if self.is_list:
            format = format[1:-1]  # remove brackets
        self.format = format.lower().split(',')
        self.colormap = colormap
        self.labelmap = labelmap

    def draw_bbox_on(self, boxes, img) -> np.ndarray:
        if hasattr(boxes, 'numpy'):
            boxes = boxes.numpy()

        if self.is_list:
            for box in boxes:
                img = self._draw(box, img)
        else:
            img = self._draw(boxes, img)
        return img

    def _draw(self, bbox, img):
        def get(spec):
            if spec in self.format:
                ind = self.format.index(spec)
                return bbox[ind]
            return None

        img_h, img_w = img.shape[:2]

        x1 = get('x1')
        y1 = get('y1')
        x2 = get('x2')
        y2 = get('y2')
        center_x = get('x')
        center_y = get('y')
        width = get('w')
        height = get('h')
        cls = get('cls')

        if x1 is None:
            x1 = center_x - width / 2

        if y1 is None:
            y1 = center_y - height / 2

        if x2 is None:
            x2 = center_x + width / 2

        if y2 is None:
            y2 = center_y + height / 2

        if self.relative:
            x1 *= img_w
            y1 *= img_h
            x2 *= img_w
            y2 *= img_h

        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

        if self.colormap is not None:
            color = self.colormap[cls]
        else:
            color = (255, 0, 0)

        if cls is not None and self.labelmap is not None:
            label = f"{cls}" if self.labelmap is None else self.labelmap[cls]
        else:
            label = None
        plotBBox(img, x1, y1, x2, y2, color, label=label)
        return img
