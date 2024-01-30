import colorama
import re
import threading
from pathlib import Path
from typing import Iterator, TextIO, Any, Iterable
import multiprocessing as mp


class ThreadPrinter(TextIO):
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

    def write(self, value: str) -> int:
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
        return 1

    def __eq__(self, other: object) -> bool:
        assert hasattr(self, "stream")
        return other is self.stream

    def flush(self) -> None:
        self.stream.flush()

    def __enter__(self) -> "ThreadPrinter":
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.stream.__exit__(exc_type, exc_value, traceback)

    def __iter__(self) -> Iterator[str]:
        return iter(self.stream)

    def __next__(self) -> str:
        return next(self.stream)

    def close(self) -> None:
        self.stream.close()

    def fileno(self) -> int:
        return self.stream.fileno()

    def isatty(self) -> bool:
        return self.stream.isatty()

    def read(self, __n: int = -1) -> str:
        return super().read(__n)

    def readable(self) -> bool:
        return self.stream.readable()

    def readline(self, limit: int = -1) -> str:
        return self.stream.readline(limit)

    def readlines(self, hint: int = -1) -> list[str]:
        return self.stream.readlines(hint)

    def seek(self, __offset: int, __whence: int = -1) -> int:
        return super().seek(__offset, __whence)

    def seekable(self) -> bool:
        return self.stream.seekable()

    def tell(self) -> int:
        return super().tell()

    def truncate(self, __size: int | None = None) -> int:
        return super().truncate(__size)

    def writable(self) -> bool:
        return self.stream.writable()

    def writelines(self, __lines: Iterable[str]) -> None:
        for line in __lines:
            self.write(line + "\n")


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
