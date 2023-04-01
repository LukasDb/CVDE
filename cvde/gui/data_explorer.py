import numpy as np
import logging
import streamlit as st
import os
import json
import cv2
import pandas as pd
import cvde.data_types as dt
from cvde.workspace import Workspace as WS
from cvde.workspace_tools import load_dataset, load_config, load_dataspec


def visualize_image(handle, img):
    img_shape = img.shape

    if img.dtype == np.uint8 or img.dtype == np.uint16:
        pass
    else:
        img = cv2.convertScaleAbs(img, alpha=255 / np.max(img))
        img = cv2.applyColorMap(img, cv2.COLORMAP_JET)

    h, w = img.shape[:2]

    scale = max(h // 120, 1)
    img = cv2.resize(img, (w // scale, h // scale))

    handle.image(img, caption=f"Shape: {img_shape}")


@st.cache_resource
def get_cached_dataset(data_mod, data_config):
    dataset = load_dataset(data_mod, data_config)
    return dataset

def visualize_datapoint(spec, data, handle = st):
    if isinstance(spec, dict):
        for k,v in spec.items():
            if isinstance(k, str):
                handle.write(k)
                visualize_datapoint(v, data[k])
            else:
                raise NotImplementedError("Dict with non string keys!")

    elif isinstance(spec, (tuple, list)):
        for i, (subspec, subdata) in enumerate(zip(spec, data)):
            handle.write(i)
            visualize_datapoint(subspec, subdata)

    elif isinstance(spec, dt.Image):
        vis = spec.get_visualization(data)
        handle.image(vis, caption=f"Shape: {data.shape}")

    elif isinstance(spec, dt.Batch):
        cols = handle.columns(spec.batch_size)
        for col, i in zip(cols, range(spec.batch_size)):
            visualize_datapoint(spec.inner_spec, data[i], handle=col)

    elif isinstance(spec, dt.Numerical):
        st.write(data)

    else:
        raise AssertionError('Unkonwn entry in spec: ', spec)


def data_explorer():
    st.title("Data Explorer")

    data_loaders = WS().datasets
    configs = WS().configs
    # build data viewer
    col1, col2, col3 = st.columns(3)
    data_mod = col1.selectbox('Data source', data_loaders)
    config_name = col2.selectbox('Config', configs)
    is_val = col3.checkbox('Use val_data_config')

    # reloads page, progresses through iterable dataset
    buttons = col3.columns(2)
    buttons[0].button("Next")
    # reset dataset to 0
    buttons[1].button("Reset", on_click=lambda: st.cache_resource.clear())

    config = load_config(config_name)
    key = 'val_config' if is_val else 'train_config'
    data_config = config[key]

    with st.spinner("Loading data..."):
        dataset = get_cached_dataset(data_mod, data_config)
        data_spec = load_dataspec(data_mod, data_config) 

        for i, d in enumerate(dataset):
            visualize_datapoint(data_spec, d)
            break