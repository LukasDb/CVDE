import logging
import os
import pathlib
import subprocess
import click
from pathlib import Path
import cvde


@click.group()
def run() -> None:
    "Computer Vision Development Environment"
    pass


@run.command()
@click.option("-n", "--name", help="Name of the workspace")
def init(name: str) -> None:
    "Create an empty workspace"
    cvde.Workspace.init_workspace(name)


@run.command()
@click.option("-p", "--port", default="8501", help="Port to access the GUI", show_default=True)
@click.argument("ROOT", type=click.Path(exists=True, path_type=pathlib.Path), default=os.getcwd())
def gui(port: int, root: Path) -> None:
    "Run CVDE GUI in your browser"

    gui_file = Path(__file__).parent / "gui.py"

    streamlit_config = [
        # "--server.runOnSave",
        # "true",
        "--server.port",
        str(port),
    ]

    proc = subprocess.Popen(
        ["streamlit", "run", str(gui_file.resolve()), *streamlit_config],
        cwd=root,
    )

    try:
        while proc.poll() is None:
            logging.info(proc.communicate())

    except KeyboardInterrupt:
        logging.warning("User interrupted.")
    finally:
        proc.kill()
