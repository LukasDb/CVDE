import os
from st_on_hover_tabs import on_hover_tabs
import streamlit as st

from gui.dashboard import dashboard
from gui.data_explorer import data_explorer


def main():
    st.set_page_config(layout="wide")
    st.header("CVDE")
    st.markdown('<style>' + open(os.path.join(os.path.dirname(__file__),
                'style.css')).read() + '</style>', unsafe_allow_html=True)

    with st.sidebar:
        tabs = on_hover_tabs(tabName=['Dashboard', 'Data Explorer', 'Model Explorer'],
                             iconName=['dashboard', 'images', 'model_training'], default_choice=0)

    if tabs == 'Dashboard':
        dashboard()

    elif tabs == 'Data Explorer':
        data_explorer()

    elif tabs == 'Model Explorer':
        st.title("Model Explorer")
        st.write('Name of option is {}'.format(tabs))


if __name__ == '__main__':
    main()
