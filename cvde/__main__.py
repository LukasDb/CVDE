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
from job_handler import execute_job

@click.group()
def run():
    "Computer Vision Development Enviroment"
    pass

@run.command()
@click.argument('task')
@click.argument('config')
def execute(task, model, train_data, val_data, config):
    "Execute a given task"
    execute_job(task=task, config=config, model_name=model,
                train_ds=train_data, val_ds=val_data)



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


    try:
        while proc.poll() is None:
            logging.info(proc.communicate(1.0))

    except KeyboardInterrupt:
        logging.warning("User interrupted.")
    finally:
        proc.kill()

def summary():
    print(get_ws_summary())
