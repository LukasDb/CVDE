import pandas as pd
from cvde.job_tracker import JobTracker, LogEntry
import streamlit as st
import os
import yaml
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from typing import List


class JobInspector:
    TAGS = ['final', 'notable', 'testing']

    def __init__(self) -> None:
        try:
            self.runs = os.listdir('log')
        except FileNotFoundError:
            self.runs = []
        st.subheader("Runs")
        self._trackers = [JobTracker.from_log(run) for run in self.runs]
        self._trackers.sort(key=lambda t:t.started, reverse=True)

    def run(self):
        # assemble settings in sidebar
        with st.sidebar:
            st.subheader("Settings")
            use_time = st.checkbox("Use actual time")
            selected_tags = st.multiselect("Filter by tags", options=self.TAGS)
            cols = st.columns(2)
            cols[0].subheader("Logged runs")
            all_selected = cols[1].checkbox("Select all")

        # filter for selected trackers
        if len(selected_tags) > 0:
            self._trackers = [t for t in self._trackers if any(
                tag in selected_tags for tag in t.tags)]
        if len(self._trackers) == 0:
            st.info("No runs found.")

        # assemble gui for filtered trackers
        self.trackers: List[JobTracker] = []
        for tracker in self._trackers:
            in_progress = '🔴 ' if tracker.in_progress else ""
            unique_name = f"{in_progress}{tracker.name} ({tracker.started})"
            with st.sidebar:
                if st.checkbox(unique_name, key=tracker.folder_name, value=all_selected):
                    self.trackers.append(tracker)

        # extract variable names
        var_names = []
        [var_names.extend(t.vars) for t in self.trackers]
        var_names = np.unique(var_names)

        # display data
        # for each variable name, assemble plot of data
        for var_name in var_names:
            for t in self.trackers:
                run_data = t.read_var(var_name)
    
                key = 't' if use_time else 'index'
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
                    y = np.expand_dims(y, -1) # add channel to channel less images

                if len(y.shape) == 4:
                    # visualize as image
                    with st.expander(var_name):
                        if len(y)>1:
                            epoch = st.slider('Epoch', min_value=0, max_value=len(y)-1, key=var_name, value=len(y)-1)
                        else:
                            epoch = 0
                        y = y[epoch]
                        channel_dim = np.argmin(y.shape)
                        other_dims = [i for i in range(3) if i != channel_dim]
                        transp = [*other_dims, channel_dim]
                        img = np.transpose(y, transp)

                        if y.shape[channel_dim] == 1:
                            img = (img.astype(float) * 255 / np.max(img)).astype(np.uint8)
                        else:
                            img = y

                        st.image(img)

                elif len(y.shape) == 1:
                    fig = go.Figure()
                    fig.add_scatter(x=x, y=y,
                                    name=unique_name, showlegend=True)
                    with st.expander(var_name):
                        st.plotly_chart(fig)

        with st.expander("Config"):
            selected_trackers = [
                t for t in self.trackers if st.session_state[t.folder_name]]
            if len(selected_trackers) == 0:
                return
            cols = st.columns(len(selected_trackers))
            for col, tracker in zip(cols, selected_trackers):
                col.text(f"{tracker.name} ({tracker.started})")
                with col:
                    st.code(yaml.dump(tracker.config), language='yaml')

        with st.expander("Set tags"):
            cols = st.columns(len(selected_trackers))
            for tracker, col in zip(selected_trackers, cols):
                set_tags = st.multiselect(
                    "Tags", self.TAGS, default=tracker.tags)
                tracker.set_tags(set_tags)
