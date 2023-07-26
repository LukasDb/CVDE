import traceback
from itertools import cycle
import numpy as np
import logging
import streamlit as st
import os
import json
import cv2
import pandas as pd

import cvde
from cvde.workspace import Workspace as WS
import cvde.workspace_tools as ws_tools
from typing import Tuple, Iterable


@st.cache_resource
def get_cached_dataset(dataset: cvde.tf.Dataset, **kwargs) -> cvde.tf.Dataset:
    dataset_fn = cvde.tf.Dataset.load_dataset(dataset)
    dataset = dataset_fn(**kwargs)
    return dataset


@st.cache_data
def get_data(_dataset, data_index):
    return next(_dataset)


def inc_data_index():
    st.session_state.data_index += 1


def dec_data_index():
    st.session_state.data_index -= 1


def reset():
    st.cache_resource.clear()
    st.cache_data.clear()
    st.session_state.data_index = 0


def data_explorer():
    if "data_index" not in st.session_state:
        st.session_state["data_index"] = 0
    if "max_data" not in st.session_state:
        st.session_state["max_data"] = 1

    data_loaders = [x.__name__ for x in WS().datasets]
    configs = WS().configs

    # build data viewer
    col1, col2, col3 = st.columns(3)
    dataset_name = col1.selectbox("Data source", data_loaders, on_change=reset)
    config_name = col2.selectbox("Config", configs, on_change=reset)

    # reloads page, progresses through iterable dataset
    buttons = col3.columns(3)
    buttons[0].button("Prev", on_click=dec_data_index)
    buttons[1].button("Next", on_click=inc_data_index)
    buttons[2].button("Reset", on_click=reset)

    config = ws_tools.load_config(config_name)
    config = config.get(dataset_name, {})

    if dataset_name is None:
        return

    with st.spinner("Loading data..."):
        dataset = get_cached_dataset(dataset_name, **config)
        data = get_data(dataset, int(st.session_state.data_index))

    st.subheader(f"#{st.session_state.data_index}", anchor=False)
    dataset.visualize_example(data)
