import pandas as pd
from workspace import Workspace as WS
import streamlit as st
import streamlit_ace as st_ace
import time
import pathlib


class JobEditor:
    ace_options = {
        "language": "yaml",
        "show_gutter": False,
        "auto_update": True,
        "theme": "tomorrow_night",
        "min_lines": 5,
        "tab_size": 2,
    }

    def run(self):
        cfg_name = st.selectbox("Configuration", options=WS().jobs)

        job_path = pathlib.Path("jobs/" + cfg_name + ".yml")
        with job_path.open() as F:
            job = F.read()

        text = st_ace.st_ace(job, **self.ace_options, key="current_job")

        with job_path.open("w") as F:
            F.write(text)
