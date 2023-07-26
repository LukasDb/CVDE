import time
import signal
import os

import streamlit as st
import streamlit_scrollable_textbox as stx
import subprocess
from datetime import datetime

from typing import List
from cvde.job import Job
from cvde.workspace import Workspace as WS

import multiprocessing as mp


def dashboard():
    try:
        running_jobs: List[Job] = st.session_state["jobs"]
        # runs = os.listdir("log")
        # trackers = [job.JobTracker.from_log(run) for run in runs]
        # trackers = [t for t in trackers if t.in_progress]
        # trackers.sort(key=lambda t: t.started, reverse=True)
    except KeyError:
        running_jobs = []
        # trackers = []

    for job in running_jobs:
        if not job.tracker.in_progress:
            st.session_state["jobs"].remove(job)

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
                stdout = "\n".join(t.get_stdout().split("\n")[-3:])
                st.text("stdout")
                st.code(stdout)
            except Exception:
                pass

            try:
                stderr = "\n".join(t.get_stderr().split("\n")[-5:])
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
