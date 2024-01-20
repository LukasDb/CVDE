import colorama
import re
import threading
from pathlib import Path
from typing import TextIO
import multiprocessing as mp


class ThreadPrinter:
    """multiprocessing printer in different colors, with optional file output"""

    COLORS = [
        colorama.Fore.RED,
        colorama.Fore.GREEN,
        colorama.Fore.YELLOW,
        colorama.Fore.BLUE,
        colorama.Fore.MAGENTA,
        colorama.Fore.CYAN,
    ]

    def __init__(self, stream: TextIO) -> None:
        # note: file_paths is not synchronized across processes, but because each process
        #      only needs to access its own file_path, this is not a problem
        self.file_paths: dict[str, Path] = {}
        self.reset_color = colorama.Fore.RESET
        self.stream = stream

    def register_new_out(self, file_path: Path) -> None:
        self.file_paths[mp.current_process().name] = file_path

    def write(self, value: str) -> None:
        result = re.search("[0-9]+", mp.current_process().name)
        chosen_index = 0 if result is None else int(result.group())
        chosen_color = self.COLORS[chosen_index % len(self.COLORS)]
        is_main = mp.parent_process() is None
        color = colorama.Fore.WHITE if is_main else chosen_color

        self.stream.write(color + value + self.reset_color)
        self.stream.flush()

        if mp.current_process().name in self.file_paths:
            file_path = self.file_paths[mp.current_process().name]
            with file_path.open("a") as F:
                F.write(value)

    def __eq__(self, other: object) -> bool:
        assert hasattr(self, "stream")
        return other is self.stream

    def flush(self) -> None:
        self.stream.flush()


class __ThreadPrinter:
    def __init__(self, stream: TextIO) -> None:
        self.file_outs: dict[int, TextIO] = {}
        self.colors: dict[int, colorama.Fore] = {}
        self.stream = stream
        self.encoding = stream.encoding
        self._lock = threading.Lock()
        self._colors = [
            colorama.Fore.RED,
            colorama.Fore.GREEN,
            colorama.Fore.YELLOW,
            colorama.Fore.BLUE,
            colorama.Fore.MAGENTA,
            colorama.Fore.CYAN,
        ]
        self.last_color_i = 0

    def register_new_out(self, filepath: Path) -> None:
        with self._lock:
            cur = threading.currentThread().ident
            assert isinstance(cur, int)
            self.file_outs[cur] = filepath.open("w")
            self.colors[cur] = self._colors[self.last_color_i % len(self._colors)]
            self.last_color_i += 1

    def write(self, value: str) -> None:
        current = threading.currentThread().ident
        assert current is not None
        with self._lock:
            try:
                color = self.colors[current]
            except KeyError:
                color = colorama.Fore.WHITE

            self.stream.write(color)
            self.stream.flush()
            self.stream.write(value)
            self.stream.flush()
            try:
                file = self.file_outs[current]
                file.write(value)
                file.flush()
            except KeyError:
                pass

    def __eq__(self, other: object) -> bool:
        assert hasattr(self, "stream")
        return other is self.stream

    def flush(self) -> None:
        current = threading.currentThread().ident
        assert isinstance(current, int)
        with self._lock:
            try:
                file = self.file_outs[current]
                file.flush()
            except KeyError:
                return
            self.stream.flush()
