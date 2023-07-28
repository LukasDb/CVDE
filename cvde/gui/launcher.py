import time
import subprocess
import streamlit as st
import streamlit_ace as st_ace
import pandas as pd
from typing import OrderedDict
import pathlib

import cvde
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
        buttons = st.columns([1, 1, 1, 1, 1])
        job_names = [x.__name__ for x in WS().jobs]
        job_name = buttons[0].selectbox("Job", job_names, label_visibility="collapsed")
        config_name = buttons[1].selectbox("Config", WS().configs, label_visibility="collapsed")

        if buttons[2].button("Launch", use_container_width=True):
            self.launch_job(job_name, config_name)

        if config_name is None:
            return

        config_path = pathlib.Path("configs/" + config_name + ".yml")
        with config_path.open() as F:
            config = F.read()
        new_config = st_ace.st_ace(config, **self.ace_options, key="ace_" + config_name)
        if new_config != config:
            with config_path.open("w") as F:
                F.write(new_config)

    def launch_job(self, job_name, config_name):
        WS().reload_modules()
        job_fn = cvde.job.Job.load_job(job_name)
        job = job_fn(config_name=config_name)
        job.launch()
        st.info(f"Job {job_name} launched.")
