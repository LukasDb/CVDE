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

import cvde
from .job_submission import JobSubmission


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
        self._name = meta["name"]
        self.job_name = meta["job"]
        self.started = meta["started"]
        self.tags = meta["tags"]
        self.pid = int(meta.get("pid", -1))
        self.root = Path("log/" + self.folder_name).resolve()
        self.var_root = self.root / "vars"
        self.weights_root = self.root / "weights"
        self.workspace = self.root / "workspace"
        self.stdout_file = self.root / "stdout.txt"
        self.stderr_file = self.root / "stderr.txt"

    @staticmethod
    def from_log(folder_name: str) -> "RunLogger":
        tracker = RunLogger(folder_name)
        return tracker

    @staticmethod
    def create(submission: JobSubmission) -> "RunLogger":
        """creates folder structure for run"""
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")

        unique_hash = hash(now) + sys.maxsize + 1
        folder_name = submission.run_name + "_" + str(unique_hash)
        root = Path("log/" + folder_name)

        # create subfolders
        var_root = root / "vars"
        weights_root = root / "weights"
        workspace = root / "workspace"
        var_root.mkdir(parents=True, exist_ok=True)
        weights_root.mkdir(parents=True, exist_ok=True)
        workspace.mkdir(parents=True, exist_ok=True)

        # create empty stdout, stderr files
        stdout_file = root / "stdout.txt"
        stderr_file = root / "stderr.txt"
        stdout_file.touch()
        stderr_file.touch()

        # save commit hash and diff
        if cvde.Workspace().git_tracking_enabled:
            assert submission.commit is not None
            with (root / "commit.txt").open("w") as F:
                F.write(submission.commit)

            assert submission.diff is not None
            if len(submission.diff) > 0:
                with (root / "uncommitted.diff").open("w") as F:
                    F.write(submission.diff)

        # copy job config; to preserve comments, dont dump yaml
        job_config_path = root / "job.yml"
        with job_config_path.open("w") as F:
            yaml.dump(submission.config, F)

        # create meta
        started = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        meta = {
            "job": submission.job_name,
            "name": submission.run_name,
            "started": started,
            "pid": str(mp.current_process().pid),
            "tags": submission.tags,
        }

        with (root / "log.json").open("w") as F:
            json.dump(meta, F, indent=2)

        tracker = RunLogger(folder_name)
        return tracker

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value
        with (self.root / "log.json").open() as F:
            data = json.load(F)
        data["name"] = value
        with (self.root / "log.json").open("w") as F:
            json.dump(data, F, indent=2)

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

        var = np.nan_to_num(var, copy=True)

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
