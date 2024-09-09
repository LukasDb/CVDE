import json
import subprocess
import yaml
import importlib
import os
import shutil
import logging
from datetime import datetime
import pathlib
import streamlit as st
import cvde
import inspect

from cvde.gui import notify


@st.cache_resource
def persistent_stop_queue() -> set:
    return set()


class Workspace:
    _instance: "Workspace|None" = None
    FOLDERS = ["models", "dataloaders", "jobs", "losses", "configs", "log"]
    default_git_ignore = [
        "**/__pycache__",
        "*.pt",
        "*.pyc",
        "__pycache__/",
        ".vscode/**",
        ".mypy_cache/**",
        "*.so",
        "*.o",
        "log/",
    ]

    def __new__(cls) -> "Workspace":
        if cls._instance is None:
            cls._instance = super(Workspace, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        self.name = pathlib.Path(os.getcwd()).name
        self.git_tracking_enabled = pathlib.Path(".git").exists()

    @staticmethod
    def init_workspace(name: str) -> None:

        logging.info("Creating CVDE workspace...")
        if len(os.listdir()) > 0:
            logging.error("Directory is not empty!")
            exit(-1)

        if not Workspace().git_tracking_enabled:
            print("Git tracking is disabled.")
            Workspace().enable_git_tracking()
            exit(0)

        for folder in Workspace.FOLDERS:
            os.makedirs(folder)

        # TODO generate .gitignore

        Workspace().create_debug_configs()
        Workspace().enable_git_tracking()

    def create_debug_configs(self) -> None:
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
        cvde_gui_path = pathlib.Path(cvde.main_gui.__file__).resolve()

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

    def enable_git_tracking(self) -> None:
        if input("Enable git tracking? (y/n): ").lower() != "y":
            return

        # check if git is installed
        if shutil.which("git") is None:
            logging.error("Git is not installed! Please install git and run 'cvde init' again.")
            exit(-1)

        # check if gitignore exists
        if not pathlib.Path(".gitignore").exists():
            print("Creating .gitignore...")
            with pathlib.Path(".gitignore").open("w") as F:
                F.write("\n".join(Workspace.default_git_ignore))
        else:
            print("Found existing .gitignore, appending CVDE defaults...")
            with open(".gitignore") as F:
                ignored = F.read().split("\n")
            for to_add in filter(lambda x: x not in ignored, Workspace.default_git_ignore):
                ignored.append(to_add)
            with open(".gitignore", "w") as F:
                F.write("\n".join(ignored))

        print("CVDE will create a branch called 'experiments' and commit your runs there.")
        new_repo = False
        # check if current repo exists
        if not pathlib.Path(".git").exists():
            print("Creating new git repository...")
            subprocess.run(["git", "init"])
            new_repo = True

        if new_repo:
            # only add changes if repo is new
            subprocess.run(["git", "add", "--all"])
            subprocess.run(["git", "commit", "-m", "initial commit"])

    def list_jobs(self) -> dict[str, type[cvde.job.Job]]:
        """find Names of cvde.job.Job subclasses in jobs/"""

        def is_cvde_job(cls: type) -> bool:
            return inspect.isclass(cls) and issubclass(cls, cvde.job.Job)

        jobs: dict[str, type[cvde.job.Job]] = {}
        for file in pathlib.Path("jobs").iterdir():
            if file.is_file() and file.suffix == ".py" and file.stem != "__init__":
                submodule = importlib.import_module(f"jobs.{file.stem}")
                importlib.reload(submodule)
                ds = inspect.getmembers(submodule, is_cvde_job)
                jobs.update({d[0]: d[1] for d in ds if not d[0].startswith("_")})
        return jobs

    def list_configs(self) -> dict[str, dict | None]:
        configs: dict[str, dict | None] = {}
        for file in pathlib.Path("configs").iterdir():
            if file.is_file() and file.suffix == ".yml":
                with file.open() as F:
                    try:
                        config: dict | None = yaml.load(F, Loader=yaml.Loader)
                    except Exception:
                        config = None

                    configs[file.stem] = config
        return configs

    def list_dataloaders(self) -> dict[str, type[cvde.tf.Dataset]]:
        def is_cvde_dataset(cls: type) -> bool:
            return inspect.isclass(cls) and issubclass(cls, cvde.tf.Dataset)

        dataloaders: dict[str, type[cvde.tf.Dataset]] = {}

        try:
            contents = list(pathlib.Path("dataloaders").iterdir())
        except FileNotFoundError:
            if pathlib.Path("datasets").exists():
                warning = (
                    "WARNING: 'datasets' folder is deprecated, please rename it to 'dataloaders'"
                )
                notify(warning)
                logging.error(warning)
            raise ValueError(f"Could not find folder 'dataloader'! ({warning})")

        for file in contents:
            if file.is_file() and file.suffix == ".py" and file.stem != "__init__":
                submodule = importlib.import_module(f"dataloaders.{file.stem}")
                importlib.reload(submodule)
                ds = inspect.getmembers(submodule, is_cvde_dataset)
                dataloaders.update({d[0]: d[1] for d in ds if not d[0].startswith("_")})
        return dataloaders
