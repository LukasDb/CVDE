import streamlit as st
from workspace import Workspace as WS
import workspace_tools as ws_tools


class ModelExplorer:
    def run(self):
        c1, c2 = st.columns(2)
        model_name = c1.selectbox("Model", WS().models)
        job_name = c2.selectbox("Job", WS().jobs)
        cfg = load_config(job_name)
        model = load_model(model_name, **cfg)
        st.write(model)

        del model
