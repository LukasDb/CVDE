import colorama
import threading
from pathlib import Path


class ThreadPrinter:
    def __init__(self, stream):
        self.file_outs = {}
        self.colors = {}
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

    def register_new_out(self, filepath: Path):
        with self._lock:
            cur = threading.currentThread().ident
            self.file_outs[cur] = filepath.open("w")
            self.colors[cur] = self._colors[self.last_color_i % len(self._colors)]
            self.last_color_i += 1

    def write(self, value):
        with self._lock:
            try:
                color = self.colors[threading.currentThread().ident]
            except KeyError:
                color = colorama.Fore.WHITE

            self.stream.write(color)
            self.stream.flush()
            self.stream.write(value)
            self.stream.flush()
            try:
                file = self.file_outs[threading.currentThread().ident]
                file.write(value)
                file.flush()
            except KeyError:
                pass

    def __eq__(self, other):
        return other is self.stream

    def flush(self):
        with self._lock:
            try:
                file = self.file_outs[threading.currentThread().ident]
                file.flush()
            except KeyError:
                return
            self.stream.flush()
