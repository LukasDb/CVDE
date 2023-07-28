import time
import signal
import os

import streamlit as st
import streamlit_scrollable_textbox as stx
import subprocess
from datetime import datetime

from typing import List
from cvde.job import Job, JobTracker
from cvde.workspace import Workspace as WS

import multiprocessing as mp


def dashboard():
    try:
        runs = os.listdir("log")
        trackers = [JobTracker.from_log(run) for run in runs]
        trackers = [t for t in trackers if t.in_progress]
        trackers.sort(key=lambda t: t.started, reverse=True)
    except KeyError:
        trackers = []
        
    running_jobs = [Job.load_job(t.name)(folder_name=t.folder_name) for t in trackers]

    with st.expander("Runs", expanded=True):
        for j in running_jobs:
            t = j.tracker
            c1, c2 = st.columns([8, 1])
            c1.markdown(f"**{t.display_name}**")

            kill_button = c2.empty()
            clicked_kill = kill_button.button("Kill", key="kill_job_" + t.unique_name)
            if clicked_kill:
                kill_button.button("Confirm?", key="confirm_kill_job_" + t.unique_name)

            if st.session_state.get("confirm_kill_job_" + t.unique_name, False):
                st.warning(f"Killing {t.name}")
                j.stop()

                time.sleep(0.5)
                st.experimental_rerun()

            try:
                stdout = "\n".join(t.get_stdout().split("\n")[-1:])
                st.text("stdout")
                st.code(stdout)
            except Exception:
                pass

            try:
                stderr = "\n".join(t.get_stderr().split("\n")[-1:])
                st.text("stderr")
                st.code(stderr)
            except Exception:
                pass

            st.divider()

    with st.expander("Workspace Overview"):
        st.subheader("Workspace Overview", anchor=False)
        st.code(WS().summary())

    with st.expander("Device Status", expanded=True):
        smi = subprocess.run(["nvidia-smi"], capture_output=True).stdout.decode()

        st.subheader("Device Status", anchor=False)
        st.code(smi)
