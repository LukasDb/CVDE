import pandas as pd
from cvde.job_tracker import JobTracker
import streamlit as st
import os
import numpy as np
import plotly.graph_objects as go
import plotly.express as px


class JobInspector:
    def __init__(self) -> None:
        self.runs = os.listdir('log')

    def run(self):
        st.title("Job Tracker")


        vars = {}
        # load data
        with st.sidebar:
            st.subheader("Settings")
            use_time = st.checkbox("Use actual time")
            st.subheader("Logged runs")

    
        for run in self.runs:
            with st.sidebar:
                if not st.checkbox(run, key=run):
                    continue
            #st.info(f"{run} tracked")
            tracker = JobTracker.from_log(run)
            for var in tracker.vars:
                vars.setdefault(var, {})
                unique_name = f"{tracker.configuration.name} ({run})"
                vars[var][unique_name] = tracker.read_var(var)
        
        # display data
        for var_name, data in vars.items():
            fig = go.Figure()
            for run_name, run_data in data.items():
                key = 't' if use_time else 'index'
                x_data = np.array([x[key] for x in run_data])
                y_data = np.array([x['data'].numpy() for x in run_data])
                #fig = px.line(x=x_data, y=y_data)
                fig.add_scatter(x=x_data,y=y_data, name=run_name, showlegend=True)
            with st.expander(var_name):
                st.plotly_chart(fig)