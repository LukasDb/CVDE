import pandas as pd
from cvde.job_tracker import JobTracker, LogEntry
import streamlit as st
import os
import yaml
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from typing import List
import time


class JobInspector:
    TAGS = ['final', 'notable', 'testing']

    def __init__(self) -> None:
        self.expanders = {}
        self.img_epochs = {}

        try:
            self.runs = os.listdir('log')
            self.all_trackers = [JobTracker.from_log(run) for run in self.runs]
            self.all_trackers.sort(key=lambda t: t.started, reverse=True)
        except Exception:
            self.runs = []
        st.subheader("Runs")


    def run(self):
        trackers = self.get_selected_trackers()
        trackers.sort(key=lambda t: t.started, reverse=True)

        # extract variable names
        var_names = []
        [var_names.extend(t.vars) for t in trackers]
        var_names = np.unique(var_names)

        if len(trackers) > 0:
            num_epochs = list([len(x.read_var(x.vars[0])) for x in trackers])
            self.max_epoch = max(num_epochs)

        # display data
        # for each variable name, assemble plot of data

        for var_name in var_names:
            fig = None
            for t in trackers:
                try:
                    run_data = t.read_var(var_name)
                except FileNotFoundError:
                    continue

                key = 't' if self.use_time else 'index'
                x = np.array([getattr(i, key) for i in run_data])
                y = [i.data for i in run_data]

                # convert tensors to numpy
                if hasattr(y[0], 'cpu'):
                    y = [i.cpu() for i in y]
                if hasattr(y[0], 'detach'):
                    y = [i.detach() for i in y]
                if hasattr(y[0], 'numpy'):
                    y = [i.numpy() for i in y]

                y = np.array(y)

                if len(y.shape) == 3:
                    # add channel to channel less images
                    y = np.expand_dims(y, -1)

                if len(y.shape) == 4:
                    self.visualize_image_with_controls(
                        var_name, y, t.unique_name)

                elif len(y.shape) == 1:
                    if fig is None:
                        fig = go.Figure()

                    fig.add_scatter(x=x, y=y,
                                    name=t.unique_name, showlegend=True)
                    exp = self.get_expander(var_name, default=st.empty)
                    if self.log_axes:
                        fig.update_yaxes(type="log")
                    exp.plotly_chart(fig)

        conf_exp = st.expander("Config")
        if len(trackers) == 0:
            return
        cols = conf_exp.columns(len(trackers))
        for col, tracker in zip(cols, trackers):
            col.text(f"{tracker.name} ({tracker.started})")
            col.code(yaml.dump(tracker.config), language='yaml')

        tags_exp = st.expander("Set tags")
        cols = tags_exp.columns(len(trackers))
        for tracker, col in zip(trackers, cols):
            set_tags = col.multiselect(
                f"Tags: {tracker.unique_name}", self.TAGS, default=tracker.tags)
            tracker.set_tags(set_tags)

    def get_selected_trackers(self):
        # assemble settings in sidebar
        with st.sidebar:
            st.subheader("Settings")
            self.use_time = st.checkbox("Use actual time")
            self.log_axes =st.checkbox('Log axes', value=True)
            selected_tags = st.multiselect("Filter by tags", options=self.TAGS)
            cols = st.columns(2)
            cols[0].subheader("Logged runs")
            all_selected = cols[1].checkbox("Select all")

        # filter by tags
        if len(selected_tags) > 0:
            self.all_trackers = [t for t in self.all_trackers if any(
                tag in selected_tags for tag in t.tags)]

        # gui + select runs
        trackers: List[JobTracker] = []
        for tracker in self.all_trackers:
            with st.sidebar:
                if st.checkbox(tracker.unique_name, value=all_selected):
                    trackers.append(tracker)

        with st.sidebar:
            [st.text('') for i in range(10)]
            if st.button('delete selected (permanently)'):
                for t in trackers:
                    t.delete_log()
                time.sleep(0.5)
                st.experimental_rerun()
        return trackers

    def get_expander(self, var_name, default=None):
        if var_name not in self.expanders:
            self.expanders[var_name] = exp = st.expander(var_name)

            if default is not None:
                with exp:
                    container = default()
                # overwrite to internal container
                self.expanders[var_name] = container

        return self.expanders[var_name]

    def visualize_image_with_controls(self, var_name, imgs, caption):
        exp = self.get_expander(var_name)

        if var_name not in self.img_epochs:
            epoch = 0
            if self.max_epoch > 1:
                epoch = exp.slider('select', min_value=0, label_visibility='hidden',
                                    max_value=self.max_epoch - 1, key=var_name, value=self.max_epoch - 1)

            self.img_epochs[var_name] = epoch

        try:
            epoch = self.img_epochs[var_name]
            img = imgs[epoch]
        except Exception:
            exp.error(f"Not enough datapoints {caption}")
            return

        channel_dim = np.argmin(img.shape)
        other_dims = [i for i in range(3) if i != channel_dim]
        transp = [*other_dims, channel_dim]
        img = np.transpose(img, transp)

        exp.image(img, caption=caption)
