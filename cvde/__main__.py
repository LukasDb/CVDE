import logging
import sys
import os
import subprocess
import json
import importlib
import threading
import time
import click

from cvde.workspace import Workspace as WS
from cvde.job.job_executor import JobExecutor


@click.group()
def run():
    "Computer Vision Development Enviroment"
    pass


@run.command()
@click.argument("name")
def execute(name):
    "Execute a given task"
    JobExecutor.run_job(name)


@run.command()
@click.argument("type")
@click.argument("name")
def create(type, name):
    "Create a new module of type {data|model|config|task}"
    create(type, name)


@run.command()
@click.option("-n", "--name", help="Name of the workspace")
def init(name):
    "Create an empty workspace"
    WS().init_workspace(name)


@run.command()
@click.option(
    "-p", "--port", default="8501", help="Port to access the GUI", show_default=True
)
def gui(port):
    "Run CVDE GUI in your browser"
    gui_file = os.path.join(os.path.dirname(__file__), "gui.py")
    streamlit_config = [
        "--server.runOnSave",
        "true",
        "--server.port",
        port,
        "--theme.base",
        "dark",
    ]

    proc = subprocess.Popen(["streamlit", "run", gui_file, *streamlit_config])

    try:
        while proc.poll() is None:
            logging.info(proc.communicate(timeout=1.0))

    except KeyboardInterrupt:
        logging.warning("User interrupted.")
    finally:
        proc.kill()


def summary():
    print(WS().summary())
