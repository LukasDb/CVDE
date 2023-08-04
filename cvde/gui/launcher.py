import time
import subprocess
import streamlit as st
import streamlit_ace as st_ace
from streamlit_tags import st_tags
import pandas as pd
from typing import List
import pathlib

import cvde
import cvde.gui
from cvde.workspace import Workspace as WS
from cvde.workspace import ModuleExistsError
import cvde.workspace_tools as ws_tools


class Launcher:
    ace_options = {
        "language": "yaml",
        "show_gutter": False,
        "auto_update": True,
        "theme": "tomorrow_night",
        "min_lines": 5,
        "tab_size": 2,
    }

    def __init__(self) -> None:
        self.configs = list(WS().configs)
        self.configs.sort()

    def run(self):
        top_row = st.columns([1, 1, 1, 1, 1])
        bottom_row = st.columns([1, 1, 1, 1, 1])

        job_names = [x.__name__ for x in WS().jobs]
        job_name = bottom_row[0].selectbox("Job", job_names)
        config_name = bottom_row[1].selectbox("Config", WS().configs)
        run_name = bottom_row[2].text_input(
            "Run",
            placeholder=job_name + "_" + config_name,
            help="To help distinguish runs with similar configs, you can give your experiment a custom name.",
        )
        with bottom_row[3]:
            tags = st_tags(
                label="Tags",
                text="Add tags...",
                value=[],
            )


        if len(run_name) == 0:
            run_name = job_name + "_" + config_name

        if top_row[0].button("Launch", use_container_width=True):
            self.launch_job(job_name, config_name, run_name, tags=tags)

        if config_name is None:
            return

        config_path = pathlib.Path("configs/" + config_name + ".yml")
        with config_path.open() as F:
            config = F.read()
        new_config = st_ace.st_ace(config, **self.ace_options, key="ace_" + config_name)
        if new_config != config:
            with config_path.open("w") as F:
                F.write(new_config)

    def launch_job(self, job_name, config_name, run_name, tags: List[str]):
        WS().reload_modules()
        job_fn = cvde.job.Job.load_job(job_name)
        job = job_fn(config_name=config_name, run_name=run_name, tags=tags)
        job.launch()
        cvde.gui.notify(f"Launching job '{job_name}' with config '{config_name}' and run name '{run_name}'.")
