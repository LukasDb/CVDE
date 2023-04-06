import traceback
from itertools import cycle
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


@st.cache_resource
def get_cached_dataset(data_mod, **kwargs):
    dataset = load_dataset(data_mod, **kwargs)
    if hasattr(dataset, '__iter__'):
        dataset = dataset.__iter__()
    return dataset


@st.cache_data
def get_data(_dataset, data_index):
    return next(_dataset)


def get_vis_stack(spec, data, stacks: dict, batch_ind=0):
    """ walks through data_spec and builds settings gui as well as assembling a stack of correlated data"""
    if isinstance(spec, dict):
        for k, v in spec.items():
            if isinstance(k, str):
                st.write(k)
                stacks = get_vis_stack(v, data[k], stacks, batch_ind)
            else:
                raise NotImplementedError("Dict with non string keys!")
        return stacks

    elif isinstance(spec, (tuple, list)):
        for inner_spec, inner_data in zip(spec, data):
            stacks = get_vis_stack(
                inner_spec, inner_data, stacks, batch_ind)
        return stacks

    elif isinstance(spec, dt.Batch):
        for batch_n, batch_data in enumerate(data):
            stacks.setdefault(batch_n, {})
            stacks = get_vis_stack(
                spec.inner_spec, batch_data, stacks, batch_ind=batch_n)
        return stacks

    elif isinstance(spec, dt.Image):
        vis = spec.get_visualization(data)
        name_str = f"{spec.name}, " if spec.name is not None else ""
        name_str += f"Shape: {data.shape}"
        is_first_image = 'image' not in [x['type']
                                         for x in stacks[batch_ind].values()]

        # only create GUI for 'first' data in batch
        if batch_ind == 0:
            if is_first_image:
                st.session_state[spec.name] = 1.0
            else:
                st.slider(f"Overlay: {spec.name}", key=spec.name)

        stacks[batch_ind].update({spec.name: {'data': vis, 'type': 'image'}})
        return stacks

    elif isinstance(spec, dt.Numerical):
        stacks[batch_ind].update(
            {spec.name: {'data': data, 'type': 'numerical'}})
        if batch_ind == 0:
            st.session_state[spec.name] = True
        return stacks

    elif isinstance(spec, dt.Bbox):
        if batch_ind == 0:
            st.checkbox(spec.name, key=spec.name)
        stacks[batch_ind].update(
            {spec.name: {'spec': spec, 'data': data, 'type': 'bbox'}})
        return stacks

    elif spec is None:
        pass
    else:
        raise AssertionError('Unkonwn entry in spec: ', spec)


def inc_data_index():
    st.session_state.data_index += 1


def dec_data_index():
    st.session_state.data_index -= 1


def reset():
    st.cache_resource.clear()
    st.cache_data.clear()
    st.session_state.data_index = 0


def data_explorer():
    st.title("Data Explorer")

    if 'data_index' not in st.session_state:
        st.session_state['data_index'] = 0
    if 'max_data' not in st.session_state:
        st.session_state['max_data'] = 1

    data_loaders = WS().datasets
    configs = WS().configs
    # build data viewer
    col1, col2, col3 = st.columns(3)
    dataset_name = col1.selectbox('Data source', data_loaders, on_change=reset)
    config_name = col2.selectbox('Config', configs, on_change=reset)
    is_val = col3.checkbox('Use val_data_config', on_change=reset)

    # reloads page, progresses through iterable dataset
    buttons = col3.columns(3)
    buttons[0].button("Prev", on_click=dec_data_index)
    buttons[1].button("Next", on_click=inc_data_index)
    buttons[2].button("Reset", on_click=reset)

    config = load_config(config_name)
    key = 'val_config' if is_val else 'train_config'
    data_config = config[key]


    with st.spinner("Loading data..."):
        # Loading spec and cached data
        dataset = get_cached_dataset(
            dataset_name, **data_config, **config['shared'])
        data_spec = load_dataspec(
            dataset_name, **data_config, **config['shared'])
        data = get_data(dataset, int(st.session_state.data_index))

    # build settings and assemble organized visualizations
    with st.sidebar:
        st.subheader('Settings')

        stacks = {0: {}}
        try:
            stacks = get_vis_stack(data_spec, data, stacks=stacks)
        except Exception:
            st.error('Is your dataspec correct?')
            def get_shape(x):
                if hasattr(x, 'shape'):
                    return x.shape
                elif isinstance(x, (list, tuple)):
                    return [get_shape(i) for i in x]
                elif isinstance(x, dict):
                    return {k:get_shape(v) for k,v in x.items()}
                else:
                    return x
            data_shape = get_shape(data)
            st.error(f"Received: {data_shape}")


    # visualizing the data

    st.subheader(f"#{st.session_state.data_index}")

    cols = st.columns(2)
    for stack, col in zip(stacks.values(), cycle(cols)):
        image_data = None
        captions = []
        with col:
            for name, data in stack.items():
                if not st.session_state[name]:
                    continue

                if data['type'] == 'image':
                    if image_data is None:
                        image_data = data['data']
                        captions.append(f"Shape: {image_data.shape}")
                    else:
                        α = st.session_state[name] / 100.
                        image_data = cv2.addWeighted(
                            image_data, 1 - α, data['data'], α, 0)
                    captions.append(name)

                elif data['type'] == 'bbox':
                    image_data = data['spec'].draw_bbox_on(
                        data['data'], image_data)
                    captions.append(name)

                elif data['type'] == 'numerical':
                    num = data['data']
                    if hasattr(num, 'numpy'):
                        num = num.numpy()
                    st.text(f"{name}: {num}")

            if image_data is not None:
                st.image(image_data, caption=" - ".join(captions))
