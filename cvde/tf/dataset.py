from typing import Any, Iterable, Dict
from abc import abstractmethod, ABC
import numpy as np
from typing import TYPE_CHECKING


class Dataset:
    def __iter__(self):
        return self

    @abstractmethod
    def visualize_example(self, example) -> None:
        """Specify how to visualize on (unbatched) example from the dataset
        Use streamlit to visualize the example

        Args:
            example (as returned by this Dataset): Python object yielded by this Dataset

        """
        pass

    @abstractmethod
    def __len__(self)->int:
        pass

    @abstractmethod
    def __next__(self):
        pass

    @abstractmethod
    def to_tf_dataset(self):
        pass
