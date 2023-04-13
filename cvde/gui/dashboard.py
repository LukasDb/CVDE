import signal
import os
import streamlit as st
import subprocess
from datetime import datetime

from cvde.job_tracker import JobTracker
from cvde.workspace import Workspace as WS
from cvde.workspace_tools import get_ws_summary


def dashboard():
    with st.expander("Creator"):
        col1, col2, col3 = st.columns((1, 2, 1))
        col1.markdown("Add new dataset:")
        dataset_name = col2.text_input('dataset name')
        col3.button("+", key='ds_btn',
                    on_click=lambda: WS().new('datasets', dataset_name, from_template=True))

        col1, col2, col3 = st.columns((1, 2, 1))
        col1.markdown("Add new config:")
        config_name = col2.text_input('config name')
        col3.button("+", key='cfg_btn',
                    on_click=lambda: WS().new('configs', config_name, from_template=True))

        col1, col2, col3 = st.columns((1, 2, 1))
        col1.markdown("Add new model:")
        model_name = col2.text_input('model name')
        col3.button("+", key='model_btn',
                    on_click=lambda: WS().new('models', model_name, from_template=True))

        col1, col2, col3 = st.columns((1, 2, 1))
        col1.markdown("Add new task:")
        task_name = col2.text_input('task name')
        col3.button("+", key='task_btn',
                    on_click=lambda: WS().new('tasks', task_name, from_template=True))

    try:
        runs = os.listdir('log')

        trackers = [JobTracker.from_log(run) for run in runs]
        trackers = [t for t in trackers if t.in_progress]
        trackers.sort(key=lambda t: t.started, reverse=True)
    except FileNotFoundError:
        trackers = []

    with st.expander('Runs', expanded=True):
        for t in trackers:
            c1, c2 = st.columns([3,1])
            with c1:
                st.markdown(f"**{t.unique_name}**")
            with c2:
                clicked = st.button("Kill", key='kill_job_' + t.name)
                if clicked:
                    pid = t.pid
                    os.kill(pid, signal.SIGINT)
            try:
                stderr = t.get_stderr()
                st.text('stderr')
                st.code(stderr)
            except Exception:
                pass
            try:
                stdout = t.get_stdout()
                st.text('stdout')
                st.code(stdout)
            except Exception:
                pass
            st.divider()

    with st.expander('Workspace Overview'):
        st.subheader("Workspace Overview")
        st.code(get_ws_summary())

    with st.expander('Device Status', expanded=True):
        smi = subprocess.run(
            ['nvidia-smi'], capture_output=True).stdout.decode()

        st.subheader('Device Status')
        st.code(smi)
