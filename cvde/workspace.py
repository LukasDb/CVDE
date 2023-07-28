import json
import yaml
import numpy as np
import os
import shutil
import logging
import importlib
from datetime import datetime
from enum import Enum, auto
from typing import Any, List, Callable
import pathlib
import inspect
import tensorflow as tf
import sys
import threading


import cvde
import cvde.workspace_tools as ws_tools


class ModuleExistsError(Exception):
    pass


class Workspace:
    stop_queue = None
    lock = None

    _instance = None
    FOLDERS = [
        "models",
        "datasets",
        "jobs",
        "losses",
        "configs",
    ]

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Workspace, cls).__new__(cls, *args, **kwargs)
            cls.stop_queue = set()
            cls.lock = threading.Lock()
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

        for folder in self.FOLDERS:
            os.makedirs(folder)
            with open(os.path.join(folder, "__init__.py"), "w") as F:
                F.write("")

        # change/add .vscode launch config for debugging
        try:
            with pathlib.Path(".vscode/launch.json").open() as F:
                launch_config = json.load(F)
        except FileNotFoundError:
            launch_config = {
                "version": "0.2.0",
                "configurations": [],
            }

        # check if launch config already exists
        add_pytest = True
        add_gui_debug = True
        for config in launch_config["configurations"]:
            if config["name"] == "Python: PyTest":
                add_pytest = False
            if config["name"] == "Python: CVDE GUI":
                add_gui_debug = False

        pytest_path = shutil.which("pytest")
        streamlit_path = shutil.which("streamlit")
        cvde_gui_path = pathlib.Path(__file__).parent / "gui.py"

        if add_pytest and pytest_path is not None:
            launch_config["configurations"].append(
                {
                    "name": "Python: PyTest",
                    "type": "python",
                    "request": "launch",
                    "program": pytest_path,
                    "console": "integratedTerminal",
                    "justMyCode": True,
                }
            )

        if add_gui_debug:
            launch_config["configurations"].append(
                {
                    "name": "Python: CVDE GUI",
                    "type": "python",
                    "request": "launch",
                    "program": streamlit_path,
                    "args": ["run", str(cvde_gui_path.resolve())],
                    "justMyCode": True,
                }
            )

        pathlib.Path(".vscode/").mkdir(exist_ok=True)
        with pathlib.Path(".vscode/launch.json").open("w") as F:
            json.dump(launch_config, F, indent=4)

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
            lambda v: (inspect.isclass(v) and issubclass(v, tf.keras.losses.Loss))
            or hasattr(v, "__call__"),
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

    def reload_modules(self):
        # reload all modules in Workspace
        loaded = sys.modules.copy()
        for mod in loaded:
            for folder in self.FOLDERS:
                if mod.startswith(folder) or mod == folder:
                    importlib.reload(sys.modules[mod])
