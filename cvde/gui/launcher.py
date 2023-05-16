import time
import subprocess
from cvde.workspace import Workspace as WS
from cvde.workspace import ModuleExistsError
from cvde.job.job_executor import JobExecutor
import streamlit as st
import streamlit_ace as st_ace
import pandas as pd
from typing import OrderedDict
from cvde.workspace_tools import load_job
import pathlib


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
        self.jobs = list(WS().jobs)
        self.jobs.sort()

    def run(self):
        buttons = st.columns([1, 1, 1, 1, 1])
        job_name = buttons[0].selectbox("Job", WS().jobs, label_visibility='collapsed')
        if buttons[1].button("Add Job",  use_container_width=True):
            self.add_job()
        if buttons[2].button("Duplicate", use_container_width=True):
            self.duplicate_job(job_name)
        if buttons[3].button("Delete", use_container_width=True):
            self.delete_job(job_name)
        if buttons[4].button("Launch", use_container_width=True):
            self.launch_job(job_name)

        job_path = pathlib.Path("jobs/" + job_name + ".yml")
        with job_path.open() as F:
            job = F.read()
        new_job = st_ace.st_ace(job, **self.ace_options, key='ace_'+job_name)
        if new_job != job:
            with job_path.open("w") as F:
                F.write(new_job)

    def duplicate_job(self, job_name):
        job_path = pathlib.Path("jobs/" + job_name + ".yml")
        new_job_path = pathlib.Path("jobs/" + job_name + "_copy.yml")
        with job_path.open() as F:
            job = F.read()

        with new_job_path.open("w") as F:
            F.write(job)

    def launch_job(self, job_name):
        JobExecutor.launch_job(job_name)
        st.info(f"Job {job_name} launched.")

    
    def delete_job(self, job_name):
        job_path = pathlib.Path("jobs/" + job_name + ".yml")
        job_path.unlink()
        time.sleep(0.5)
        st.experimental_rerun()



    def update_config(self, name, type):
        new_job_config = self.jobs[name]
        val = st.session_state[name + "__" + type]
        new_job_config[type] = val
        self.delete_job(name)
        WS().new("jobs", name, job=new_job_config)

    def change_name(self, name):
        job = self.jobs[name]
        new_name = st.session_state[name + "name"]
        try:
            WS().new("jobs", new_name, job=job)
            self.delete_job(name)
        except ModuleExistsError:
            st.error("Job already exists! Rename previous copy to a unique name.")




    def add_empty_job(self):
        WS().new("jobs", "New Job")


