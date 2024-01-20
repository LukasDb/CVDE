import streamlit as st
import streamlit_ace as st_ace  # type: ignore
from streamlit_tags import st_tags  # type: ignore
import pathlib
import datetime
import multiprocessing as mp
import os
from typing import Any
import sys

import cvde
from cvde.workspace import Workspace as WS
from .page import Page

import tensorflow as tf


class Launcher(Page):
    ace_options = {
        "language": "yaml",
        "show_gutter": False,
        "auto_update": True,
        "theme": "tomorrow_night",
        "min_lines": 5,
        "tab_size": 2,
    }

    def __init__(self) -> None:
        if "tags" not in st.session_state:
            st.session_state.tags = set()
        pass

    def run(self) -> None:
        self.configs = WS().list_configs()
        self.configs.sort()
        top_row = st.columns(5)
        bottom_row = st.columns(5)

        job_names = WS().list_jobs()
        job_name = bottom_row[0].selectbox("Job", job_names)
        assert isinstance(job_name, str)
        config_name = bottom_row[1].selectbox("Config", self.configs)
        assert isinstance(config_name, str)
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        default_run_name = f"{now}_{job_name}_{config_name}"
        run_name = bottom_row[2].text_input(
            "Run",
            placeholder=default_run_name,
            help="To help distinguish runs with similar configs, you can give your experiment a custom name.",
        )
        with bottom_row[3]:
            tags = st_tags(
                label="Tags",
                text="Add tags...",
                value=[],
                suggestions=list(st.session_state.tags),
            )

        if len(run_name) == 0:
            run_name = default_run_name

        launch = top_row[0].button("Launch", use_container_width=True)
        env_string = top_row[1].text_input(
            "Environment",
            value="CUDA_VISIBLE_DEVICES=0",
            help="Set environment variables and separate with semicolons.",
        )
        env = {
            key.strip(): value.strip()
            for key, value in [word.split("=") for word in env_string.split(";")]
        }

        if config_name is None:
            return

        config_path = pathlib.Path("configs/" + config_name + ".yml")
        with config_path.open() as F:
            config = F.read()
        new_config = st_ace.st_ace(config, **self.ace_options, key="ace_" + config_name)
        if new_config != config:
            with config_path.open("w") as F:
                F.write(new_config)

        if launch:
            mp.Process(
                # target=_run,
                target=_run,
                kwargs={
                    "job_name": job_name,
                    "config_name": config_name,
                    "run_name": run_name,
                    "tags": tags,
                    "env": env,
                },
                daemon=True,
            ).start()

            cvde.gui.notify(
                f"Launching job '{job_name}' with config '{config_name}' and run name '{run_name}'."
            )

    def on_leave(self) -> None:
        return super().on_leave()


def _run(job_name: str, run_name: str, config_name: str, tags: list[str], env: dict) -> None:
    """in new Process"""
    for k, v in env.items():
        os.environ[k] = v

    job_fn = cvde.ws_tools.load_job(job_name)
    job = job_fn(config_name=config_name, run_name=run_name, tags=tags)

    def handler(sig: int, frame: Any) -> None:
        print("Terminated by user.")
        job.on_terminate()

    import signal

    signal.signal(signal.SIGTERM, handler)

    assert isinstance(sys.stdout, cvde.ThreadPrinter)
    assert isinstance(sys.stderr, cvde.ThreadPrinter)

    # print sdtout, err to files as well
    sys.stdout.register_new_out(job.tracker.stdout_file)
    sys.stderr.register_new_out(job.tracker.stderr_file)

    job.run()
