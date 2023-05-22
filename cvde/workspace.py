import json
import yaml
import os
import logging
import importlib
from datetime import datetime
from enum import Enum, auto
import sys
from typing import Any, List, Callable
import pathlib
import inspect
import tensorflow as tf

import cvde

sys.path.append(os.getcwd())


class ModuleExistsError(Exception):
    pass


class Workspace:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Workspace, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self) -> None:
        try:
            self._read_state()
        except FileNotFoundError:
            pass

    def init_workspace(self, name: str) -> None:
        logging.info("Creating empty workspace...")
        if len(os.listdir()) > 0:
            logging.error("Workspace is not empty!")
            exit(-1)

        self.name: str = name
        self.created: str = datetime.now().strftime("%Y-%m-%d")

        state = {"name": self.name, "created": self.created}
        with open(".workspace.cvde", "w") as F:
            json.dump(state, F, indent=4)

        folders = [
            "models",
            "datasets",
            "jobs",
            "optimizers",
            "losses",
            "callbacks",
            "metrics",
        ]
        for folder in folders:
            os.makedirs(folder)
            with open(os.path.join(folder, "__init__.py"), "w") as F:
                F.write("")

    def _read_state(self):
        with open(".workspace.cvde") as F:
            state = json.load(F)
        self.name = state["name"]
        self.created = state["created"]

    def _list_modules(self, base_module: str, condition: Callable[[Any], bool]):
        loaded = sys.modules.copy()
        for mod in loaded:
            if mod.startswith(base_module):
                del sys.modules[mod]

        files = list(
            x
            for x in pathlib.Path(base_module).iterdir()
            if x.is_file() and not x.stem.startswith("_")
        )
        datasets = []

        for file in files:
            module = importlib.import_module(base_module + "." + file.stem)
            try:
                importlib.reload(module)
            except ImportError:
                pass
            datasets.extend(
                [
                    k
                    for k, v in module.__dict__.items()
                    if condition(v) and not k.startswith("_")
                ]
            )
        return datasets

    @property
    def datasets(self):
        return self._list_modules(
            "datasets", lambda v: inspect.isclass(v) and issubclass(v, cvde.tf.Dataset)
        )

    @property
    def models(self):
        return self._list_modules(
            "models", lambda v: inspect.isclass(v) and issubclass(v, tf.keras.Model)
        )

    @property
    def jobs(self):
        dir = "jobs"
        jobs = list(x.stem for x in pathlib.Path(dir).glob("*.yml"))
        return jobs

    @property
    def losses(self):
        return self._list_modules(
            "losses",
            lambda v: inspect.isclass(v) and issubclass(v, tf.keras.losses.Loss),
        )

    @property
    def callbacks(self):
        return self._list_modules(
            "callbacks",
            lambda v: inspect.isclass(v) and issubclass(v, tf.keras.callbacks.Callback),
        )

    @property
    def metrics(self):
        return self._list_modules(
            "metrics",
            lambda v: inspect.isclass(v) and issubclass(v, tf.keras.metrics.Metric),
        )

    @property
    def optimizers(self):
        return self._list_modules(
            "optimizers",
            lambda v: inspect.isclass(v)
            and issubclass(v, tf.keras.optimizers.Optimizer),
        )

    def summary(self) -> str:
        # print summary of workspace
        out = ""
        out += "-- Workspace summary --\n"
        out += "Created: " + self.created + "\n"

        def print_entries(type):
            entries = ""
            for m in self.__getattribute__(type):
                entries += f"├───{m}\n"
            return entries

        out += "\nJobs:\n"
        out += print_entries("jobs")

        out += "\nDataloaders:\n"
        out += print_entries("datasets")

        out += "\nModels:\n"
        out += print_entries("models")

        out += "\nLosses:\n"
        out += print_entries("losses")

        out += "\nMetrics:\n"
        out += print_entries("metrics")

        out += "\nCallbacks:\n"
        out += print_entries("callbacks")

        return out
