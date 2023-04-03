import pandas as pd
from cvde.job_tracker import JobTracker
import streamlit as st
import os
import yaml
import numpy as np
import plotly.graph_objects as go
import plotly.express as px


class JobInspector:
    def __init__(self) -> None:
        try:
            self.runs = os.listdir('log')
        except FileNotFoundError:
            self.runs = []
        st.subheader("Runs")
        st.info("No runs found.")
        self.trackers = [JobTracker.from_log(run) for run in self.runs]

    def run(self):
        vars = {}
        # load data
        with st.sidebar:
            st.subheader("Settings")
            use_time = st.checkbox("Use actual time")
            st.subheader("Logged runs")

        for tracker in self.trackers:
            unique_name = f"{tracker.name} ({tracker.started})"
            with st.sidebar:
                if not st.checkbox(unique_name, key=tracker.folder_name):
                    continue
            # st.info(f"{run} tracked")
            for var in tracker.vars:
                vars.setdefault(var, {})
                vars[var][unique_name] = tracker.read_var(var)

        # display data
        for var_name, data in vars.items():
            fig = go.Figure()
            for unique_name, run_data in data.items():
                key = 't' if use_time else 'index'
                x_data = np.array([x[key] for x in run_data])
                y_data = np.array([x['data'].numpy() for x in run_data])
                # fig = px.line(x=x_data, y=y_data)
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
