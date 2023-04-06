import os
from st_on_hover_tabs import on_hover_tabs
import streamlit as st
from cvde.workspace import Workspace as WS


def main():
    st.set_page_config(
        layout="wide",
        page_title=WS()['name'],
            menu_items={
        'Get Help': 'https://github.com/LukasDb/CVDE',
        'Report a bug': "https://github.com/LukasDb/CVDE/issues",
        'About': "Tool to manage CV experiments and training deep learning models."
    })
    st.header(WS()['name'])
    style_file = os.path.join(os.path.dirname(__file__), 'style.css')
    with open(style_file) as F:
        style = F.read()
    st.markdown(f"<style>{style}</style>", unsafe_allow_html=True)

    pages = ['Dashboard', 'Data Explorer', 'Model Explorer',
             'Config Editor', 'Job Manager', 'Inspector', 'Deployment']

    if 'selected_page' not in st.session_state:
        st.session_state['selected_page'] = pages[0]
    cols = st.columns(len(pages))
    for col, page in zip(cols, pages):
        with col:
            st.write("""<div class='PortMarker'/>""", unsafe_allow_html=True)
            if st.button(f"**{page}**"):
                st.session_state['selected_page'] = page

    st.markdown('---')

    def title(t):
        # c1, c2 = st.columns(2)
        st.title(t)
        st.button('⟳', key=t + '_reload')

    sel_p = st.session_state['selected_page']
    if sel_p == 'Dashboard':
        title('Dashboard')
        from cvde.gui.dashboard import dashboard
        dashboard()

    elif sel_p == 'Data Explorer':
        from cvde.gui.data_explorer import data_explorer
        data_explorer()

    elif sel_p == 'Model Explorer':
        title("Model Explorer")
        st.markdown('An overview over the models in the workspace')

    elif sel_p == 'Config Editor':
        title('Config Editor')
        from cvde.gui.config_editor import ConfigEditor
        ce = ConfigEditor()
        ce.run()

    elif sel_p == 'Job Manager':
        title('Job Manager')
        from cvde.gui.job_manager import JobManager
        jm = JobManager()
        jm.run()

    elif sel_p == "Inspector":
        title("Inspector")
        from cvde.gui.job_inspector import JobInspector
        jt = JobInspector()
        jt.run()

    elif sel_p == "Deployment":
        title("Deployment")
        st.markdown(
            "You can download weights here in different formats. Maybe online inference as well")


if __name__ == '__main__':
    main()
