import os
from st_on_hover_tabs import on_hover_tabs
import streamlit as st


def main():
    st.set_page_config(layout="wide")
    st.header("Computer Vision Development Environment")

    pages = ['Dashboard', 'Data Explorer', 'Model Explorer', 'Config Editor', 'Job Manager', 'Inspector', 'Deployment']

    if 'selected_page' not in st.session_state:
        st.session_state['selected_page'] = pages[0]

    cols = st.columns(len(pages))
    for col, page in zip(cols, pages):
        with col:
            if st.button(page):
                st.session_state['selected_page'] = page
               

    sel_p = st.session_state['selected_page']
    if sel_p == 'Dashboard':
        from cvde.gui.dashboard import dashboard
        dashboard()

    elif sel_p == 'Data Explorer':
        from cvde.gui.data_explorer import data_explorer
        data_explorer()

    elif sel_p == 'Model Explorer':
        st.title("Model Explorer")
        st.markdown('An overview over the models in the workspace')
    
    elif sel_p == 'Config Editor':
        from cvde.gui.config_editor import ConfigEditor
        ce = ConfigEditor()
        ce.run()

    elif sel_p == 'Job Manager':
        from cvde.gui.job_manager import JobManager
        jm = JobManager()
        jm.run()

    elif sel_p == "Inspector":
        from cvde.gui.job_inspector import JobInspector
        jt = JobInspector()
        jt.run()

    elif sel_p == "Deployment":
        st.title("Deployment")
        st.markdown(
            "You can download weights here in different formats. Maybe online inference as well")


if __name__ == '__main__':
    main()
