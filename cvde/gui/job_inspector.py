import pandas as pd
from cvde.job_tracker import JobTracker
import streamlit as st
import os
import yaml
import numpy as np
import plotly.graph_objects as go
import plotly.express as px


class JobInspector:
    TAGS = ['final', 'notable', 'testing']

    def __init__(self) -> None:
        try:
            self.runs = os.listdir('log')
        except FileNotFoundError:
            self.runs = []
        st.subheader("Runs")
        self.trackers = [JobTracker.from_log(run) for run in self.runs]


    def run(self):
        vars = {}
        # load data
        with st.sidebar:
            st.subheader("Settings")
            use_time = st.checkbox("Use actual time")
            selected_tags = st.multiselect("Filter by tags", options=self.TAGS)
            cols = st.columns(2)
            cols[0].subheader("Logged runs")
            all_selected = cols[1].checkbox("Select all")

        if len(selected_tags)>0:
            self.trackers = [t for t in self.trackers if any(tag in selected_tags for tag in t.tags)]
        
        if len(self.trackers)==0:
            st.info("No runs found.")

        for tracker in self.trackers:
            unique_name = f"{tracker.name} ({tracker.started})"
            with st.sidebar:
                if not st.checkbox(unique_name, key=tracker.folder_name, value=all_selected):
                    continue
            # st.info(f"{run} tracked")
            for var in tracker.vars:
                vars.setdefault(var, {})
                vars[var][unique_name] = tracker.read_var(var)

        # vars: {var_name: {run1: list(value), run2: list(value)}}
        # with value: {t: time, index: int, data: float/img/etc}
        # display data
        for var_name, data in vars.items():
            fig = go.Figure()
            for unique_name, run_data in data.items():
                key = 't' if use_time else 'index'
                x_data = np.array([x[key] for x in run_data])

                data_list = [x['data'] for x in run_data]

                if hasattr(data_list[0], 'cpu'):
                    data_list = [x.cpu() for x in data_list]

                if hasattr(data_list[0], 'detach'):
                    data_list = [x.detach() for x in data_list]

                if hasattr(data_list[0], 'numpy'):
                    data_list = [x.numpy() for x in data_list]

                y_data = np.array(data_list)

                fig.add_scatter(x=x_data, y=y_data,
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
                set_tags = st.multiselect("Tags", self.TAGS, default=tracker.tags)
                tracker.set_tags(set_tags)


