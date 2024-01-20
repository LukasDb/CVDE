import json
import importlib
import os
import shutil
import logging
from datetime import datetime
import pathlib
import streamlit as st
import cvde
import inspect


class ModuleExistsError(Exception):
    pass


@st.cache_resource
def persistent_stop_queue() -> set:
    return set()


class Workspace:
    _instance: "Workspace|None" = None
    FOLDERS = [
        "models",
        "datasets",
        "jobs",
        "losses",
        "configs",
    ]

    def __new__(cls) -> "Workspace":
        if cls._instance is None:
            cls._instance = super(Workspace, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        try:
            self._read_state()
        except FileNotFoundError:
            raise FileNotFoundError(
                f".workspace.cvde not found. Are you in a CVDE workspace? (Currently: {os.getcwd()})"
            )

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

    def _read_state(self) -> None:
        with open(".workspace.cvde") as F:
            state = json.load(F)
        self.name = state["name"]
        self.created = state["created"]

    def list_jobs(self) -> list[str]:
        """find Names of cvde.job.Job subclasses in jobs/"""
        jobs = []
        for file in pathlib.Path("jobs").iterdir():
            if file.is_file() and file.suffix == ".py" and file.stem != "__init__":
                jobs.append(file.stem)
        return jobs

    def list_configs(self) -> list[str]:
        configs = []
        for file in pathlib.Path("configs").iterdir():
            if file.is_file() and file.suffix == ".yml":
                configs.append(file.stem)
        return configs

    def list_datasets(self) -> dict[str, type[cvde.tf.Dataset]]:
        def is_cvde_dataset(cls: type) -> bool:
            return inspect.isclass(cls) and issubclass(cls, cvde.tf.Dataset)

        datasets: dict[str, type[cvde.tf.Dataset]] = {}
        for file in pathlib.Path("datasets").iterdir():
            if file.is_file() and file.suffix == ".py" and file.stem != "__init__":
                submodule = importlib.import_module(f"datasets.{file.stem}")
                importlib.reload(submodule)
                ds = inspect.getmembers(submodule, is_cvde_dataset)
                datasets.update({d[0]: d[1] for d in ds if not d[0].startswith("_")})
        return datasets
