import os

import tensorflow as tf

gpus = tf.config.experimental.list_physical_devices("GPU")
if gpus:
    try:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
    except RuntimeError as e:
        print(e)


import streamlit as st
from datetime import datetime
from cvde.workspace import Workspace as WS
import requests


def main():
    st.set_page_config(
        layout="wide",
        page_title=WS().name,
        menu_items={
            "Get Help": "https://github.com/LukasDb/CVDE",
            "Report a bug": "https://github.com/LukasDb/CVDE/issues",
            "About": "Tool to manage CV experiments and training deep learning models.",
        },
    )

    style_file = os.path.join(os.path.dirname(__file__), "style.css")
    with open(style_file) as F:
        style = F.read()
    st.markdown(f"<style>{style}</style>", unsafe_allow_html=True)

    pages = [
        "Dashboard",
        "Data",
        "Models",
        # "Configurator",
        "Jobs",
        "Inspector",
        "Deployment",
    ]

    if "selected_page" not in st.session_state:
        st.session_state["selected_page"] = pages[0]

    cols = st.columns(len(pages) + 1)
    cols[0].text("")
    cols[0].markdown(f"**{WS().name}**")

    for col, page in zip(cols[1:], pages):
        col.write("""<div class='PortMarker'/>""", unsafe_allow_html=True)
        if col.button(f"**{page}**", use_container_width=True):
            st.session_state["selected_page"] = page

    def title(t):
        try:
            current_weather = requests.get(
                "http://www.wttr.in", params={"format": "%c %t"}, timeout=1.0
            ).text
        except Exception:
            current_weather = ""

        st.title(t, anchor=False)
        c1, c2 = st.columns([1, 20])
        c1.button("⟳", key=t + "_reload")
        c2.markdown(
            f'{current_weather} *Last update: {datetime.now().strftime("%H:%M:%S")}*'
        )

    sel_p = st.session_state["selected_page"]
    if sel_p == "Dashboard":
        title("Dashboard")
        from cvde.gui.dashboard import dashboard

        dashboard()

    elif sel_p == "Data":
        from cvde.gui.data_explorer import data_explorer

        data_explorer()

    elif sel_p == "Models":
        title("Model Explorer")
        from cvde.gui.model_explorer import ModelExplorer

        me = ModelExplorer()
        me.run()

    elif sel_p == "Configurator":
        title("Configurator")
        from cvde.gui.job_editor import JobEditor

        ce = JobEditor()
        ce.run()

    elif sel_p == "Jobs":
        title("Jobs")
        from cvde.gui.launcher import Launcher

        jm = Launcher()
        jm.run()

    elif sel_p == "Inspector":
        title("Inspector")
        from cvde.gui.job_inspector import JobInspector

        jt = JobInspector()
        jt.run()

    elif sel_p == "Deployment":
        title("Deployment")
        from cvde.gui.deployment import Deployment

        dp = Deployment()
        dp.run()


if __name__ == "__main__":
    main()
