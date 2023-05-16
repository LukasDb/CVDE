import time
import signal
import os
import streamlit as st
import streamlit_scrollable_textbox as stx
import subprocess
from datetime import datetime

from cvde.job import job_tracker as job
from cvde.workspace import Workspace as WS

import docker


def dashboard():
    with st.expander("Creator"):
        col1, col2, col3 = st.columns((1, 2, 1))
        col1.markdown("Add new dataset:")
        dataset_name = col2.text_input("dataset name")
        col3.button(
            "+",
            key="ds_btn",
            on_click=lambda: WS().new("datasets", dataset_name, from_template=True),
        )

        col1, col2, col3 = st.columns((1, 2, 1))
        col1.markdown("Add new config:")
        config_name = col2.text_input("config name")
        col3.button(
            "+",
            key="cfg_btn",
            on_click=lambda: WS().new("configs", config_name, from_template=True),
        )

        col1, col2, col3 = st.columns((1, 2, 1))
        col1.markdown("Add new model:")
        model_name = col2.text_input("model name")
        col3.button(
            "+",
            key="model_btn",
            on_click=lambda: WS().new("models", model_name, from_template=True),
        )

        col1, col2, col3 = st.columns((1, 2, 1))
        col1.markdown("Add new task:")
        task_name = col2.text_input("task name")
        col3.button(
            "+",
            key="task_btn",
            on_click=lambda: WS().new("tasks", task_name, from_template=True),
        )

    try:
        runs = os.listdir("log")

        trackers = [job.JobTracker.from_log(run) for run in runs]
        trackers = [t for t in trackers if t.in_progress]
        trackers.sort(key=lambda t: t.started, reverse=True)
    except FileNotFoundError:
        trackers = []

    with st.expander("Runs", expanded=True):
        for t in trackers:
            c1, c2 = st.columns([8, 1])
            c1.markdown(f"**{t.display_name}**")

            kill_button = c2.empty()
            clicked_kill = kill_button.button("Kill", key="kill_job_" + t.unique_name)
            if clicked_kill:
                kill_button.button("Confirm?", key="confirm_kill_job_" + t.unique_name)

            if st.session_state.get("confirm_kill_job_" + t.unique_name, False):
                container_id = t.folder_name
                st.warning(f"Killing {container_id}")
                cont = docker.from_env().containers.get(container_id)
                cont.kill()
                time.sleep(0.5)
                cont.stop()
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
