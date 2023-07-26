import json
import yaml
import os
import logging
import importlib
from datetime import datetime
from enum import Enum, auto
from typing import Any, List, Callable
import pathlib
import inspect
import tensorflow as tf

import cvde
import cvde.workspace_tools as ws_tools


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
            "losses",
            "configs",
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

    @property
    def datasets(self):
        return ws_tools.list_modules(
            "datasets", lambda v: inspect.isclass(v) and issubclass(v, cvde.tf.Dataset)
        )

    @property
    def models(self):
        return ws_tools.list_modules(
            "models", lambda v: inspect.isclass(v) and issubclass(v, tf.keras.Model)
        )

    @property
    def configs(self):
        dir = "configs"
        configs = list(x.stem for x in pathlib.Path(dir).glob("*.yml"))
        return configs

    @property
    def jobs(self):
        return ws_tools.list_modules(
            "jobs", lambda v: inspect.isclass(v) and issubclass(v, cvde.job.Job)
        )

    @property
    def losses(self):
        return ws_tools.list_modules(
            "losses",
            lambda v: inspect.isclass(v) and issubclass(v, tf.keras.losses.Loss),
        )

    def summary(self) -> str:
        # print summary of workspace
        out = ""
        out += "-- Workspace summary --\n"
        out += "Created: " + self.created + "\n"

        def print_entries(type):
            entries = ""
            for m in self.__getattribute__(type):
                if hasattr(m, "__name__"):
                    name = m.__name__
                else:
                    name = m
                entries += f"├───{name}\n"
            return entries

        out += "\nJobs:\n"
        out += print_entries("jobs")

        out += "\nConfigs:\n"
        out += print_entries("configs")

        out += "\nDataloaders:\n"
        out += print_entries("datasets")

        out += "\nModels:\n"
        out += print_entries("models")

        out += "\nLosses:\n"
        out += print_entries("losses")


        return out
