import pickle
import json
import streamlit as st
from datetime import datetime
from cvde.workspace_tools import load_config
import os
from dataclasses import dataclass
import sys
from typing import Any, List
import shutil

# TODO this needs refactoring
# move to pathlib


@dataclass
class LogEntry:
    t: datetime
    index: int
    data: Any


@dataclass
class JobTracker:
    name: str
    task: str
    config_name: str
    model: str
    train_set: str
    val_set: str
    config: dict

    def __post_init__(self):
        self.root = None
        self.folder_name = None
        self.started = None
        self.var_root = None
        self.weights_root = None
        self.index = 0
        self.tags = []

    @staticmethod
    def from_log(folder_name):
        with open(os.path.join('log', folder_name, 'log.json')) as F:
            meta = json.load(F)

        tracker = JobTracker(meta['name'], None, None,
                             None, None, None, meta['config'])
        tracker.folder_name = folder_name
        tracker.started = meta['started']
        tracker.tags = meta['tags']
        tracker.root = os.path.join("log", tracker.folder_name)
        tracker.var_root = os.path.join(tracker.root, 'vars')
        tracker.weights_root = os.path.join(tracker.root, 'weights')
        tracker.model = meta['model']

        return tracker

    @property
    def unique_name(self):
        in_progress = '🔴 ' if self.in_progress else ""
        return f"{in_progress}{self.name} ({self.started})"

    @property
    def pid(self):
        with open(os.path.join(self.root, 'log.json')) as F:
            meta = json.load(F)
        return meta['pid']

    @property
    def in_progress(self):
        with open(os.path.join(self.root, 'log.json')) as F:
            meta = json.load(F)
        return meta['in_progress']

    def get_stderr(self):
        with open(os.path.join(self.root, 'stderr.txt')) as F:
            line = F.readlines()[-1]
        return line
    
    def get_stdout(self):
        with open(os.path.join(self.root, 'stdout.txt')) as F:
            line = F.readlines()[-1]
        return line

    @staticmethod
    def create(name: str, task: str, config_name: str, model: str, train_set: str, val_set: str):
        # use time as a unique key
        config = load_config(config_name)

        tracker = JobTracker(name, task, config_name,
                             model, train_set, val_set, config)

        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        tracker.folder_name = '_'.join(
            [now, name, task, config_name, model, train_set, val_set])
        tracker.root = os.path.join("log", tracker.folder_name)
        tracker.tags = []

        if os.path.exists(tracker.root):
            try:
                ind = int(tracker.root[-1]) + 1
            except Exception:
                ind = 1

            tracker.folder_name += f'_{ind}'
            tracker.root = os.path.join("log", tracker.folder_name)

        tracker.var_root = os.path.join(tracker.root, 'vars')
        tracker.weights_root = os.path.join(tracker.root, 'weights')
        os.makedirs(tracker.root)
        os.makedirs(tracker.var_root)
        os.makedirs(tracker.weights_root)

        tracker.meta = {
            "name": tracker.name,
            "started": None,
            "task": tracker.task,
            "model": tracker.model,
            "train Dataset": tracker.train_set,
            "val Dataset": tracker.val_set,
            "config": config,
            "in_progress": False,
            "tags": [],
            "pid": os.getpid(),
        }

        with open(os.path.join(tracker.root, 'log.json'), 'w') as F:
            json.dump(tracker.meta, F, indent=2)
        return tracker
    
    def delete_log(self):
        shutil.rmtree(self.root)

    def set_tags(self, tags):
        self.tags = tags
        self.__overwrite_meta('tags', tags)

    def __overwrite_meta(self, key, value):
        with open(os.path.join(self.root, 'log.json'), 'r') as F:
            data = json.load(F)
        data[key] = value
        with open(os.path.join(self.root, 'log.json'), 'w') as F:
            json.dump(data, F, indent=2)

    def __enter__(self):
        self.started = datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S")
        self.__overwrite_meta("in_progress", True)
        self.__overwrite_meta("started", self.started)
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        sys.stdout = open(os.path.join(self.root, 'stdout.txt'), 'w')
        sys.stderr = open(os.path.join(self.root, 'stderr.txt'), 'w')

    def __exit__(self, type, value, traceback):
        self.__overwrite_meta("in_progress", False)
        sys.stdout.close()
        sys.stderr.close()
        sys.stdout = self.stdout
        sys.stderr = self.stderr

    @property
    def vars(self):
        var_names = [x.split('.pkl')[0] for x in os.listdir(self.var_root)]
        return sorted(var_names)

    def read_var(self, var) -> list[LogEntry]:
        var_path = os.path.join(self.var_root, var + '.pkl')
        with open(var_path, 'rb') as F:
            data: List[LogEntry] = pickle.load(F)
        return data

    def log(self, name, var, index=None):
        """ log variable """
        print(f"Logging {name}...")
        var_path = os.path.join(self.var_root, name + '.pkl')
        try:
            with open(var_path, 'rb') as F:
                data = pickle.load(F)
        except FileNotFoundError:
            data = []

        index = len(data) if index is None else index

        new_data = LogEntry(t=datetime.now(), index=index, data=var)
        data.append(new_data)

        with open(var_path, 'wb') as F:
            pickle.dump(data, F)
