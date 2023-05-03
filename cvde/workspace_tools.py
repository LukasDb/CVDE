from typing import Dict
import os
import logging
import yaml
from cvde.workspace import Workspace as WS
import importlib
from typing import Callable


def load_task_fn(task_name) -> Callable:
    module_task = importlib.import_module(f"tasks.{task_name}")
    importlib.reload(module_task)
    return module_task.main


def load_config(config_name):
    with open(os.path.join('configs', config_name + '.yml')) as F:
        config: Dict = yaml.safe_load(F)

    for key in ['shared', 'task', 'model', 'train_config', 'val_config']:
        if config[key] is None:
            config[key] = {}
    return config


def write_config(config_name, config):
    with open(os.path.join('configs', config_name + '.yml'), 'w') as F:
        yaml.dump(config, F)


def load_dataset(__dataset_name, **kwargs):
    module = importlib.import_module(
        f"datasets.{__dataset_name}")
    importlib.reload(module)
    dataset = module.get_dataloader(**kwargs)
    return dataset


def load_dataspec(__data_name, **kwargs):
    module = importlib.import_module(
        f"datasets.{__data_name}")
    importlib.reload(module)
    spec = module.get_dataspec(**kwargs)
    return spec


def load_model(__model_name, **kwargs):
    module = importlib.import_module(
        f"models.{__model_name}")
    importlib.reload(module)
    model = module.get_model(**kwargs)
    return model


def get_ws_summary():
    # print summary of workspace
    out = ""
    out += "-- Workspace summary --\n"
    out += "Created: " + WS()._state['created'] + "\n"

    def print_entries(type):
        entries = ""
        for m in WS().__getattribute__(type):
            entries += f"├───{m}\n"
        return entries

    out += "\nConfigs:\n"
    out += print_entries('configs')

    out += "\nDataloaders:\n"
    out += print_entries('datasets')

    out += "\nModels:\n"
    out += print_entries('models')

    out += "\nTasks:\n"
    out += print_entries('tasks')
    out += "\n"

    out += "\nJobs:\n"
    out += print_entries('jobs')
    out += "\n"
    return out


def init_workspace(name):
    logging.info("Creating empty workspace...")

    if len(os.listdir()) > 0:
        logging.error("Workspace is not empty!")
        exit(-1)

    folders = ['models', 'tasks', 'datasets', 'configs']
    for folder in folders:
        os.makedirs(folder)
        with open(os.path.join(folder, '__init__.py'), 'w') as F:
            F.write('')

    WS().init(name)
