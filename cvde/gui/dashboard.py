import streamlit as st
import subprocess
from datetime import datetime
import lib.refresher

from cvde.workspace_tools import get_ws_summary, create


def dashboard():
    st.markdown("# Dashboard")

    col1, col2, col3 = st.columns((1, 2, 1))
    col1.markdown("Add new dataset:")
    dataset_name = col2.text_input('dataset name')
    col3.button("+", key='ds_btn',
                on_click=lambda: create('datasets', dataset_name))

    col1, col2, col3 = st.columns((1, 2, 1))
    col1.markdown("Add new config:")
    config_name = col2.text_input('config name')
    col3.button("+", key='cfg_btn',
                on_click=lambda: create('configs', config_name))

    col1, col2, col3 = st.columns((1, 2, 1))
    col1.markdown("Add new model:")
    model_name = col2.text_input('model name')
    col3.button("+", key='model_btn',
                on_click=lambda: create('models', model_name))

    st.markdown("## Workspace Overview")
    st.code(get_ws_summary())

    smi = subprocess.run(
        ['nvidia-smi'], capture_output=True).stdout.decode()

    st.markdown('## Device Status')
    st.code(smi)
