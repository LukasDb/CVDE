import streamlit as st
import subprocess
from datetime import datetime

from cvde.workspace import Workspace as WS
from cvde.workspace_tools import get_ws_summary


def dashboard():
    st.markdown("# Dashboard")

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

    st.markdown("## Workspace Overview")
    st.code(get_ws_summary())

    smi = subprocess.run(
        ['nvidia-smi'], capture_output=True).stdout.decode()

    st.markdown('## Device Status')
    st.code(smi)
