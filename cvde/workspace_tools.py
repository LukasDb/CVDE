import yaml
import importlib
import pathlib
import sys
from typing import Any, Union
import cvde
from typing import Callable
import tensorflow as tf


def list_modules(base_module: str, condition: Union[Callable[[Any], bool], None] = None) -> list:
    loaded = sys.modules.copy()
    for mod in loaded:
        if mod.startswith(base_module):
            del sys.modules[mod]

    files = list(
        x
        for x in pathlib.Path(base_module).iterdir()
        if x.is_file() and not x.stem.startswith("_")
    )
    modules = []

    for file in files:
        module = importlib.import_module(base_module + "." + file.stem)
        try:
            importlib.reload(module)
        except ImportError:
            pass

        for k, v in module.__dict__.items():
            try:
                if condition is None or (not k.startswith("_") and condition(v)):
                    modules.append(v)
            except Exception as e:
                print("Module", k, "failed with", e)
                print(v)
                raise e
    return modules


def load_module(
    base_module: str, module_name: str
) -> Union[type["cvde.Dataset"], type["cvde.job.Job"]]:
    modules = list_modules(base_module, lambda x: getattr(x, "__name__", "") == module_name)
    if len(modules) == 0:
        raise ImportError(f"Could not find module {module_name} in {base_module}")
    if len(modules) > 1:
        raise ImportError(f"Found multiple modules with name {module_name} in {base_module}")
    module = modules[0]
    assert isinstance(module, type)
    return module


def load_job(__job_name: str) -> type["cvde.job.Job"]:
    module = importlib.import_module("jobs." + __job_name)
    # find cvde.job.Job subclass in module
    for k, v in module.__dict__.items():
        if isinstance(v, type) and issubclass(v, cvde.job.Job):
            return v
    raise ImportError(f"Could not find Job in {__job_name}")


def load_dataset(__dataset_name: str) -> type["cvde.Dataset"]:
    ds_module = cvde.ws_tools.load_module("datasets", __dataset_name)
    assert issubclass(ds_module, cvde.Dataset)
    return ds_module


def load_model(__model_name: str) -> "type[tf.keras.Model]":
    return load_module("models", __model_name)


def load_loss(__loss_name: str) -> "type[tf.keras.losses.Loss]":
    return load_module("losses", __loss_name)


def load_config(config_name: str) -> dict:
    with pathlib.Path("configs/" + config_name + ".yml").open() as F:
        job: dict = yaml.load(F, Loader=yaml.Loader)
    return job
