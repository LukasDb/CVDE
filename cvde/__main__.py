import logging
import sys
import os
import begin
import subprocess
import json
import importlib
from .workspace_tools import *


@begin.subcommand
def execute(task: 'which task to run', config: 'which config to pass to task'):
    config = load_config(config)

    model = importlib.import_module(
        f"models.{config['model']}").get_model(**config['model_config'])
    model.summary()

    train_set = load_dataset(config['train_set'], config['train_data_config'])
    val_set = load_dataset(config['val_set'], config['val_data_config'])

    module_task = importlib.import_module(f"tasks.{task}")
    module_task.main(model=model, train_set=train_set,
                     val_set=val_set, **config['task_config'])


@begin.subcommand
def create(type: 'datasets | models | tasks | configs', name: 'Unique name of dataloader'):
    "Create a data_loader, model or task"
    create(type, name)



@begin.subcommand
def init():
    "Create an empty workspace"
    init_workspace()


@begin.subcommand
def gui():
    "Run CVDE GUI in your browser"
    gui_file = os.path.join(os.path.dirname(__file__), "gui.py")
    proc = subprocess.Popen(["streamlit", "run", gui_file])
    try:
        while proc.poll() is None:
            logging.info(proc.communicate(1.0))

    except KeyboardInterrupt:
        logging.warning("User interrupted.")
    finally:
        proc.kill()

@begin.subcommand
def summary():
    print(get_ws_summary())


try:
    @begin.start
    @begin.logging
    def run():
        "Computer Vision Development Enviroment"
        pass

except TypeError:
    # HACK surpress printing from begins library (only in this main func)
    pass
    