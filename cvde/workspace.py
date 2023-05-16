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


from cvde.templates import realize_template
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

    def initialize(self, name) -> None:
        """create a new empty workspace"""
        self.name: str = name
        self.created: str = datetime.now().strftime("%Y-%m-%d")
        for k in self._keys:
            self.__setattr__(k, [])
        self._write_state()

    def init_workspace(name):
        logging.info("Creating empty workspace...")

        if len(os.listdir()) > 0:
            logging.error("Workspace is not empty!")
            exit(-1)

        folders = ["models", "tasks", "datasets", "configs"]
        for folder in folders:
            os.makedirs(folder)
            with open(os.path.join(folder, "__init__.py"), "w") as F:
                F.write("")

        WS().init(name)

    def _read_state(self):
        with open(".workspace.cvde") as F:
            state = json.load(F)
        self.name = state["name"]
        self.created = state["created"]

    @property
    def datasets(self):
        base_module = "datasets"
        self.__del_loaded_module(base_module)
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
                    if inspect.isclass(v)
                    and issubclass(v, cvde.tf.Dataset)
                    and not k.startswith("_")
                ]
            )
        return datasets

    @property
    def models(self):
        base_module = "models"
        self.__del_loaded_module(base_module)

        files = list(
            x
            for x in pathlib.Path(base_module).iterdir()
            if x.is_file() and not x.stem.startswith("_")
        )
        models = []
        for file in files:
            module = importlib.import_module(base_module + "." + file.stem)
            importlib.reload(module)
            models.extend(
                [
                    k
                    for k, v in module.__dict__.items()
                    if inspect.isclass(v)
                    and issubclass(v, tf.keras.Model)
                    and not k.startswith("_")
                ]
            )
        return models

    @property
    def jobs(self):
        dir = "jobs"
        jobs = list(x.stem for x in pathlib.Path(dir).glob("*.yml"))
        return jobs

    @property
    def losses(self):
        base_module = "losses"
        self.__del_loaded_module(base_module)

        files = list(
            x
            for x in pathlib.Path(base_module).iterdir()
            if x.is_file() and not x.stem.startswith("_")
        )
        losses = []
        for file in files:
            module = importlib.import_module(base_module + "." + file.stem)
            importlib.reload(module)
            losses.extend(
                [
                    k
                    for k, v in module.__dict__.items()
                    if (
                        inspect.isclass(v)
                        and issubclass(v, tf.keras.losses.Loss)
                        and not k.startswith("_")
                    )
                    or isinstance(v, Callable)
                ]
            )
        return losses

    @property
    def callbacks(self):
        base_module = "callbacks"
        self.__del_loaded_module(base_module)

        files = list(
            x
            for x in pathlib.Path(base_module).iterdir()
            if x.is_file() and not x.stem.startswith("_")
        )
        callbacks = []
        for file in files:
            module = importlib.import_module(base_module + "." + file.stem)
            importlib.reload(module)
            callbacks.extend(
                [
                    k
                    for k, v in module.__dict__.items()
                    if inspect.isclass(v)
                    and issubclass(v, tf.keras.callbacks.Callback)
                    and not k.startswith("_")
                ]
            )
        return callbacks

    @property
    def metrics(self):
        base_module = "metrics"
        self.__del_loaded_module(base_module)

        files = list(
            x
            for x in pathlib.Path(base_module).iterdir()
            if x.is_file() and not x.stem.startswith("_")
        )
        metrics = []
        for file in files:
            module = importlib.import_module(base_module + "." + file.stem)
            importlib.reload(module)
            metrics.extend(
                [
                    k
                    for k, v in module.__dict__.items()
                    if inspect.isclass(v) and issubclass(v, tf.keras.metrics.Metric)
                ]
            )
        return metrics

    @property
    def optimizers(self):
        base_module = "optimizers"
        self.__del_loaded_module(base_module)

        files = list(
            x
            for x in pathlib.Path(base_module).iterdir()
            if x.is_file() and not x.stem.startswith("_")
        )
        optimizers = []
        for file in files:
            module = importlib.import_module(base_module + "." + file.stem)
            importlib.reload(module)
            optimizers.extend(
                [
                    k
                    for k, v in module.__dict__.items()
                    if inspect.isclass(v)
                    and issubclass(v, tf.keras.optimizers.Optimizer)
                ]
            )
        return optimizers

    def _write_state(self):
        state = {"name": self.NAME, "created": self.CREATED}
        with open(".workspace.cvde", "w") as F:
            json.dump(state, F, indent=4)

    def __del_loaded_module(self, base_module):
        loaded = sys.modules.copy()
        for module in loaded:
            if module.startswith(base_module):
                del sys.modules[module]

    def ___delete(self, type, name):
        state = self._state
        state[type].pop(name)
        self._write(state)

    def ___new(self, type, name, from_template=False, job: dict = None):
        """registers new module in workspace.
        Generate a file if from_template is true
        if registering a job, enter defaults

        """
        assert type in [
            "datasets",
            "models",
            "tasks",
            "jobs",
            "configs",
        ], f"Unknown type: {type}.Must be one of data|model|task|config"

        if name in self.__getattribute__(type):
            logging.error(f"Not created: <{name}> ({type}) already exists")
            raise ModuleExistsError

        if from_template:
            realize_template(type, name)

        state = self._state
        if type == "jobs":
            if job is None:
                job = {
                    "Task": "None",
                    "Model": "None",
                    "Config": "None",
                    "Model": "None",
                    "Train Dataset": "None",
                    "Val Dataset": "None",
                }
            state[type].update({name: job})
        else:
            state[type].append(name)
        self._write(state)

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
