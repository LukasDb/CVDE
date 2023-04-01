import os
from st_on_hover_tabs import on_hover_tabs
import streamlit as st



def main():
    st.set_page_config(layout="wide")
    st.header("Computer Vision Development Environment")
    st.markdown('<style>' + open(os.path.join(os.path.dirname(__file__),
                'style.css')).read() + '</style>', unsafe_allow_html=True)

    with st.sidebar:
        tabs = on_hover_tabs(tabName=['Dashboard', 'Data Explorer', 'Model Explorer', 'Config Editor', 'Job Manager', 'Job Tracker', 'Deployment'],
                             iconName=['dashboard', 'images', 'model_training', 'settings', 'schema', 'insights', 'construction'], default_choice=0)

    if tabs == 'Dashboard':
        from gui.dashboard import dashboard
        dashboard()

    elif tabs == 'Data Explorer':
        from gui.data_explorer import data_explorer
        data_explorer()

    elif tabs == 'Model Explorer':
        st.title("Model Explorer")
        st.markdown('An overview over the models in the workspace')
    
    elif tabs == 'Config Editor':
        from gui.config_editor import ConfigEditor
        ce = ConfigEditor()
        ce.run()

    elif tabs == 'Job Manager':
        from gui.job_manager import JobManager
        jm = JobManager()
        jm.run()

    elif tabs == "Job Tracker":
        st.title("Job Tracker")
        st.markdown(
            "Tensorboard-like tracking of training processes and keeping logs")

    elif tabs == "Deployment":
        st.title("Deployment")
        st.markdown(
            "You can download weights here in different formats. Maybe online inference as well")


if __name__ == '__main__':
    main()
