import numpy as np
import logging
import streamlit as st
import os
import json
import cv2
from cvde.workspace_tools import get_modules, load_config, load_dataset, create
import pandas as pd


def visualize_image(handle, img):
    img_shape = img.shape

    if img.dtype == np.uint8 or img.dtype == np.uint16:
        pass
    else:
        img = cv2.convertScaleAbs(img, alpha=255 / np.max(img))
        img = cv2.applyColorMap(img, cv2.COLORMAP_JET)

    h, w = img.shape[:2]

    scale = max(h // 240, 1)
    img = cv2.resize(img, (w // scale, h // scale))

    handle.image(img, caption=f"Shape: {img_shape}")


@st.cache_resource
def get_dataset(data_mod, data_config):
    dataset = load_dataset(data_mod, data_config)
    return dataset


def data_explorer():
    st.title("Data Explorer")

    data_loaders = get_modules('datasets')
    configs = get_modules('configs')
    # build data viewer
    col1, col2, col3 = st.columns(3)
    data_mod = col1.selectbox('Data source', data_loaders)
    config_file = col2.selectbox('Config', configs)
    is_val = col3.checkbox('Is Validation Data?')

    # reloads page, progresses through iterable dataset
    buttons = col3.columns(2)
    buttons[0].button("Next")
    # reset dataset to 0
    buttons[1].button("Reset", on_click=lambda: st.cache_resource.clear())

    config = load_config(config_file)
    key = 'val_data_config' if is_val else 'train_data_config'
    data_config = config[key]

    with st.spinner("Loading data..."):
        dataset = get_dataset(data_mod, data_config)

        for i, d in enumerate(dataset):
            if i > 5:
                break

            if hasattr(d, '__getitem__'):
                # is iterable
                row = st.columns(len(d))
                for row_i, content in enumerate(d):
                    if hasattr(content, 'numpy'):
                        content = content.numpy()

                    if len(content.shape) == 3:
                        visualize_image(row[row_i], content)
                    else:
                        row[row_i].write(content)
