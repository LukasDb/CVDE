import streamlit as st
from workspace import Workspace as WS
from workspace_tools import load_model, load_job


class ModelExplorer:
    def run(self):
        c1, c2 = st.columns(2)
        model_name = c1.selectbox("Model", WS().models)
        job_name = c2.selectbox("Job", WS().jobs)
        cfg = load_job(job_name)
        model = load_model(model_name, **cfg)
        st.write(model)
        
        del model
