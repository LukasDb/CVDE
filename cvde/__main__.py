import logging
import os
import subprocess
import click
from pathlib import Path

from cvde.workspace import Workspace as WS


@click.group()
def run():
    "Computer Vision Development Enviroment"
    pass


@run.command()
@click.argument("name")
def execute(name):
    "Execute a given task"
    raise NotImplementedError
    #JobExecutor.run_job(name)


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

    gui_file = Path(__file__).parent / "gui.py"

    streamlit_config = [
        "--server.runOnSave",
        "true",
        "--server.port",
        port,
        # "--theme.base",
        # "dark",
    ]

    proc = subprocess.Popen(
        ["streamlit", "run", str(gui_file.resolve()), *streamlit_config],
        cwd=os.getcwd(),
    )

    try:
        while proc.poll() is None:
            logging.info(proc.communicate())

    except KeyboardInterrupt:
        logging.warning("User interrupted.")
    finally:
        proc.kill()


def summary():
    print(WS().summary())
