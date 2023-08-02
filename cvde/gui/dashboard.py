import time
import signal
import os
import re
import streamlit as st
import streamlit_scrollable_textbox as stx
import subprocess
import numpy as np
from datetime import datetime
from typing import List
from cvde.job import Job, JobTracker
from cvde.workspace import Workspace as WS


def dashboard():
    try:
        runs = os.listdir("log")
        trackers = [JobTracker.from_log(run) for run in runs]
        trackers = [t for t in trackers if t.in_progress]
        trackers.sort(key=lambda t: t.started, reverse=True)
    except KeyError:
        trackers = []

    running_jobs = [Job.load_job(t.job_name)(folder_name=t.folder_name) for t in trackers]

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
                st.info(WS().stop_queue)

                time.sleep(0.5)
                st.experimental_rerun()

            try:
                stdout = "\n".join(t.get_stdout().strip().split("\n")[-1:])
                st.text("stdout")
                st.code(stdout, language="html")
            except Exception:
                pass

            try:
                stderr = "\n".join(t.get_stderr().strip().split("\n")[-1:])
                st.text("stderr")
                st.code(stderr, language="html")
            except Exception:
                pass

            st.divider()

    with st.expander("Workspace Overview"):
        st.subheader("Workspace Overview", anchor=False)
        st.code(WS().summary(), language="html")

    with st.expander("Device Status", expanded=True):
        # smi = subprocess.run(["nvidia-smi"], capture_output=True).stdout.decode()
        # st.subheader("Device Status", anchor=False)
        # st.code(smi, language="html")

        # faster
        os.system("nvidia-smi stats -d pwrDraw,temp,gpuUtil,memUtil -c 1 > /tmp/gpu_util.txt")

        with open("/tmp/gpu_util.txt", "r") as f:
            gpu_util = f.read()
        # list with id, type, time_stamp, value
        gpu_stats = {}
        for line in gpu_util.split("\n"):
            if len(line) > 0:
                id, type, _, value = line.split(",")
                gpu_stats[id] = gpu_stats.get(id, {})
                gpu_stats[id][type] = gpu_stats[id].get(type, [])
                gpu_stats[id][type].append(float(value))

        gpu_cols = st.columns(len(gpu_stats))
        for id, data in gpu_stats.items():
            gpu_cols[int(id)].subheader(f"GPU {id}")
            for type, values in data.items():
                gpu_cols[int(id)].code(f"{type}: {np.mean(values):.3f}", language="html")
        # st.code(gpu_util, language="html")


# run this continously in a thread? to get tha latest info?