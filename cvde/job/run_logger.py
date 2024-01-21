import json
import multiprocessing as mp
from multiprocessing.process import BaseProcess
import pickle
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
import sys
from typing import Any
import shutil
import yaml

from PIL import Image
import numpy as np

from cvde import job


@dataclass
class LogEntry:
    t: datetime
    index: int
    data: Any
    is_image: bool


class RunLogger:
    def __init__(self, folder_name: str) -> None:
        with Path("log/" + folder_name + "/log.json").open("r") as F:
            meta = json.load(F)

        self.folder_name = folder_name
        self.name = meta["name"]
        self.job_name = meta["job"]
        self.started = meta["started"]
        self.tags = meta["tags"]
        self.pid = int(meta.get("pid", -1))
        self.root = Path("log/" + self.folder_name)
        self.var_root = self.root / "vars"
        self.weights_root = self.root / "weights"
        self.stdout_file = self.root / "stdout.txt"
        self.stderr_file = self.root / "stderr.txt"

    @staticmethod
    def from_log(folder_name: str) -> "RunLogger":
        tracker = RunLogger(folder_name)
        return tracker

    @staticmethod
    def create(job_name: str, config: dict[str, Any], run_name: str) -> "RunLogger":
        """creates folder structure for run"""
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")

        unique_hash = hash(now) + sys.maxsize + 1
        folder_name = run_name + "_" + str(unique_hash)
        root = Path("log/" + folder_name)

        var_root = root / "vars"
        var_root.mkdir(parents=True, exist_ok=True)
        weights_root = root / "weights"
        weights_root.mkdir(parents=True, exist_ok=True)

        stdout_file = root / "stdout.txt"
        stderr_file = root / "stderr.txt"
        stdout_file.touch()
        stderr_file.touch()

        # COPY JOB CONFIG OVER
        job_config_path = root / "job.yml"
        with job_config_path.open("w") as F:
            yaml.dump(config, F)

        started = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        meta = {
            "job": job_name,
            "name": run_name,
            "started": started,
            "pid": str(mp.current_process().pid),
            "tags": [],
        }

        with (root / "log.json").open("w") as F:
            json.dump(meta, F, indent=2)

        tracker = RunLogger(folder_name)
        return tracker

    @property
    def display_name(self) -> str:
        in_progress = "🔴 " if self.is_in_progress() else ""
        return f"{in_progress} {self.name} ({self.started})"

    def is_in_progress(self) -> bool:
        return self.pid in [p.pid for p in mp.active_children()]

    def get_mp_process(self) -> BaseProcess:
        for p in mp.active_children():
            if p.pid == self.pid:
                return p
        raise Exception("Process not found")

    @property
    def config(self) -> Any:
        with (self.root / "job.yml").open() as F:
            meta = yaml.safe_load(F)
        return meta

    def get_stderr(self) -> str:
        return self.stderr_file.read_text()

    def get_stdout(self) -> str:
        return self.stdout_file.read_text()

    def delete_log(self) -> None:
        shutil.rmtree(self.root)

    def set_tags(self, tags: list[str]) -> None:
        self.tags = tags

        with (self.root / "log.json").open() as F:
            data = json.load(F)
        data["tags"] = tags
        with (self.root / "log.json").open("w") as F:
            json.dump(data, F, indent=2)

    @property
    def vars(self) -> list[str]:
        var_names = [x.stem for x in self.var_root.iterdir()]
        return sorted(var_names)

    def read_var(self, var: str) -> list[LogEntry]:
        # this reads everything...
        files = sorted(list((self.var_root / var).glob("*.pkl")))
        data = [pickle.load(F.open("rb")) for F in files]
        data = [LogEntry(**d) for d in data]
        return data

    def log(self, name: str, var: np.ndarray, index: int | None = None) -> None:
        """log variable"""
        var_folder = self.var_root / name
        var_folder.mkdir(exist_ok=True)

        index = len(list(var_folder.iterdir())) if index is None else index

        var_path = self.var_root / name / f"{index:06}.pkl"

        if len(var.shape) >= 2:
            # save as jpg
            img_path = self.var_root / name / f"{index:06}.png"
            im = Image.fromarray(var)
            im.save(img_path)
            data = {"t": datetime.now(), "index": index, "data": str(img_path), "is_image": True}
        else:
            data = {"t": datetime.now(), "index": index, "data": var, "is_image": False}
        with var_path.open("wb") as F:
            pickle.dump(data, F)
