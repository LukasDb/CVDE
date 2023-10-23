import time
import os
import itertools as it
import streamlit as st
from cvde.job import Job, JobTracker
from cvde.workspace import Workspace as WS
from cvde.gui import warn


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
        cols = it.cycle(st.columns(2))
        for j in running_jobs:
            with next(cols) as c:
                t = j.tracker
                c1, c2 = st.columns(2)
                c2.markdown(f"**{t.display_name}**")

                kill_button = c1.empty()
                clicked_kill = kill_button.button("Stop", key="kill_job_" + t.unique_name)
                if clicked_kill:
                    kill_button.button("Confirm?", key="confirm_kill_job_" + t.unique_name)

                if st.session_state.get("confirm_kill_job_" + t.unique_name, False):
                    warn(f"Stopping {t.display_name}...")
                    j.stop()

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
        os.system("nvidia-smi > /tmp/gpu_util.txt")

        with open("/tmp/gpu_util.txt", "r") as f:
            gpu_util = f.read()
        st.code(gpu_util, language="html")
