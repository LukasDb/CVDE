import streamlit as st
from cvde.workspace import Workspace as WS
import cvde.workspace_tools as ws_tools


class ModelExplorer:
    def run(self):
        c1, c2 = st.columns(2)
        model_name = c1.selectbox("Model", WS().models)
        job_name = c2.selectbox("Job", WS().jobs)
        cfg = ws_tools.load_config(job_name)
        model = ws_tools.load_model(model_name, **cfg)
        st.write(model)

        del model
