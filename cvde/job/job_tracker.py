import pickle
import json
import streamlit as st
from datetime import datetime
import os
from pathlib import Path
from dataclasses import dataclass
import sys
from typing import Any, List
import shutil
import yaml
import threading


@dataclass
class LogEntry:
    t: datetime
    index: int
    data: Any


class JobTracker:
    def __init__(self, folder_name):
        with Path("log/" + folder_name + "/log.json").open() as F:
            meta = json.load(F)

        self.folder_name = folder_name
        self.name = meta["name"]
        self.started = meta["started"]
        self.tags = meta["tags"]
        self.root = Path("log/" + self.folder_name)
        self.var_root = self.root / "vars"
        self.weights_root = self.root / "weights"
        self.ident = meta["ident"]
        self.stdout_file = self.root / "stdout.txt"
        self.stderr_file = self.root / "stderr.txt"

    @staticmethod
    def from_log(folder_name):
        tracker = JobTracker(folder_name)
        return tracker

    @staticmethod
    def create(job_name: str):
        """creates folder structure for run"""
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")

        unique_hash = hash(now) + sys.maxsize + 1
        folder_name = job_name + "_" + str(unique_hash)
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
        job_config_path = Path("jobs") / (job_name + ".yml")
        shutil.copy(job_config_path, root / "job.yml")

        started = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        meta = {
            "name": job_name,
            "started": started,
            "tags": [],
            "ident": None,
        }

        with (root / "log.json").open("w") as F:
            json.dump(meta, F, indent=2)

        tracker = JobTracker(folder_name)
        return tracker

    @property
    def unique_name(self):
        return self.folder_name

    @property
    def display_name(self):
        in_progress = "🔴 " if self.in_progress else ""
        return f"{in_progress}{self.name} ({self.started})"

    @property
    def in_progress(self):
        # children = mp.active_children()
        # return "thread_"+self.unique_name in [c.name for c in children]
        return "thread_" + self.unique_name in threading.enumerate()

    @property
    def config(self):
        with (self.root / "job.yml").open() as F:
            meta = yaml.safe_load(F)
        return meta

    def get_stderr(self):
        return self.stderr_file.read_text()

    def get_stdout(self):
        return self.stdout_file.read_text()

    def delete_log(self):
        shutil.rmtree(self.root)

    def set_tags(self, tags):
        self.tags = tags

        with (self.root / "log.json").open() as F:
            data = json.load(F)
        data["tags"] = tags
        with (self.root / "log.json").open("w") as F:
            json.dump(data, F, indent=2)

    def set_thread_ident(self):
        # ident = threading.get_ident()
        ident = os.getpid()
        self.ident = ident
        with (self.root / "log.json").open() as F:
            data = json.load(F)
        data["ident"] = ident
        with (self.root / "log.json").open("w") as F:
            json.dump(data, F, indent=2)

    @property
    def vars(self):
        var_names = [x.stem for x in self.var_root.iterdir()]
        return sorted(var_names)

    def read_var(self, var: str) -> List[LogEntry]:
        var_name = var + ".pkl"
        with (self.var_root.joinpath(var_name)).open("rb") as F:
            data: List[LogEntry] = pickle.load(F)
        return data

    def log(self, name, var, index=None):
        """log variable"""
        var_path = self.var_root.joinpath(name + ".pkl")
        try:
            with var_path.open("rb") as F:
                data = pickle.load(F)
        except FileNotFoundError:
            data = []

        index = len(data) if index is None else index

        new_data = LogEntry(t=datetime.now(), index=index, data=var)
        data.append(new_data)

        with var_path.open("wb") as F:
            pickle.dump(data, F)
