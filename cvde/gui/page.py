from abc import ABC, abstractmethod
import gc


class Page(ABC):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def run(self) -> None:
        """run when page is loaded"""
        pass

    @abstractmethod
    def on_leave(self) -> None:
        gc.collect()
        pass
