import logging
import sys
import os
import subprocess
import json
import importlib
from .workspace_tools import *
import threading
import time
import click

@click.group()
def run():
    "Computer Vision Development Enviroment"
    pass

@run.command()
@click.argument('task')
@click.argument('config')
def execute(task, config):
    "Execute a given task with a configuration"
    config = load_config(config)

    model = importlib.import_module(
        f"models.{config['model']}").get_model(**config['model_config'])
    model.summary()

    train_set = load_dataset(config['train_set'], config['train_data_config'])
    val_set = load_dataset(config['val_set'], config['val_data_config'])

    module_task = importlib.import_module(f"tasks.{task}")
    module_task.main(model=model, train_set=train_set,
                     val_set=val_set, **config['task_config'])


@run.command()
@click.argument('type')
@click.argument('name')
def create(type, name):
    "Create a new module of type {data|model|config|task}"
    create(type, name)


@run.command()
def init():
    "Create an empty workspace"
    init_workspace()


@run.command()
@click.option('-p', '--port', default='8501', help='Port to access the GUI', show_default=True)
def gui(port):
    "Run CVDE GUI in your browser"
    gui_file = os.path.join(os.path.dirname(__file__), 'gui.py')
    proc = subprocess.Popen(["streamlit", "run", gui_file, "--server.runOnSave", "true", "--server.port", port])

    def refresher():
        path = os.path.join(os.path.dirname(__file__), 'lib', 'refresher.py')
        while True:
            time.sleep(5)
            with open(path, 'w') as F:
                F.write(f"# {time.time()}")
    t = threading.Thread(target=refresher, daemon=True)
    t.start()

    try:
        while proc.poll() is None:
            logging.info(proc.communicate(1.0))

    except KeyboardInterrupt:
        logging.warning("User interrupted.")
    finally:
        proc.kill()

def summary():
    print(get_ws_summary())
