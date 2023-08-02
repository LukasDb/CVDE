from typing import Dict, Callable
import tensorflow as tf
import yaml
import importlib
import pathlib
import sys
from typing import Any, Union
import cvde


def list_modules(base_module: str, condition: Union[Callable[[Any], bool], None] = None):
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


def load_module(base_module, module_name):
    modules = list_modules(base_module, lambda x: x.__name__ == module_name)
    if len(modules) == 0:
        raise ImportError(f"Could not find module {module_name} in {base_module}")
    if len(modules) > 1:
        raise ImportError(f"Found multiple modules with name {module_name} in {base_module}")
    return modules[0]


def load_model(__model_name) -> type[tf.keras.Model]:
    return load_module("models", __model_name)


def load_loss(__loss_name):
    return load_module("losses", __loss_name)


def load_config(config_name) -> Dict:
    with pathlib.Path("configs/" + config_name + ".yml").open() as F:
        job: Dict = yaml.safe_load(F)
    return job
