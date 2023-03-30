import json
import os
import logging
import importlib
from datetime import datetime
from .templates import generate_template, write_vs_launch_file
import sys
sys.path.append(os.getcwd())


class WS_Settings:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(WS_Settings, cls).__new__(
                cls, *args, **kwargs)
        return cls._instance

    def __getitem__(self, key):
        with open(".workspace.cvde") as F:
            ws = json.load(F)
        return ws[key]

    def update(self, update):
        """ overwrites 'workspace.cvde' """
        try:
            with open(".workspace.cvde") as F:
                ws = json.load(F)
            for key, val in update.items():
                if isinstance(update[key], list):
                    ws[key].extend(update[key])
                else:
                    ws.update(update)
        except (FileNotFoundError, json.JSONDecodeError):
            ws = update
            pass

        with open(".workspace.cvde", 'w') as F:
            json.dump(ws, F, indent=4)


def get_modules(module_type):
    return WS_Settings()[module_type]


def load_config(config_name):
    with open(os.path.join('configs', config_name + '.json')) as F:
        data = json.load(F)
    return data


def load_dataset(data_name, data_config):
    module = importlib.import_module(
        f"datasets.{data_name}")
    importlib.reload(module)

    train_set = module.get_dataloader(**data_config)
    return train_set


def get_ws_summary():
    # print summary of workspace
    out = ""
    out += "-- Workspace summary --\n"
    out += "Created: " + WS_Settings()['created'] + "\n"

    def print_entries(folder):
        entries = ""
        for m in get_modules(folder):
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
    return out


def init_workspace():
    logging.info("Creating empty workspace...")

    folders = ['models', 'tasks', 'datasets', 'configs']
    for folder in folders:
        try:
            os.makedirs(folder)
        except FileExistsError:
            logging.error("Workspace is not empty!")
            exit(-1)
        with open(os.path.join(folder, '__init__.py'), 'w') as F:
            F.write('')

    date = datetime.now().strftime('%Y-%m-%d')
    ws = {'created': date, 'models': [],
          'datasets': [], 'configs': [], 'tasks': []}
    WS_Settings().update(ws)

    write_vs_launch_file()


def create(type, name):
    assert type in ['datasets', 'models', 'tasks',
                    'configs'], f"Unknown type: {type}.Must be one of data|model|task|config"

    if name in get_modules(type):
        logging.error(f'Not created: <{name}> ({type}) already exists')
        return

    WS_Settings().update({'models': [name]})

    generate_template(type, name)
