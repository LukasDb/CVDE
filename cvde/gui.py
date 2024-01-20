import sys
import os

import streamlit as st
from datetime import datetime
import cvde
from cvde.workspace import Workspace as WS
import requests


def main():
    sys.path.append(os.getcwd())

    style_file = os.path.join(os.path.dirname(__file__), "style.css")
    with open(style_file) as F:
        style = F.read()
    st.markdown(f"<style>{style}</style>", unsafe_allow_html=True)

    pages = [
        "Dashboard",
        "Data",
        "Jobs",
        "Inspector",
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
        c2.markdown(f'{current_weather} *Last update: {datetime.now().strftime("%H:%M:%S")}*')

    sel_p = st.session_state["selected_page"]
    if sel_p == "Dashboard":
        title("Dashboard")
        db = cvde.gui.Dashboard()
        db.run()

    elif sel_p == "Data":
        title("Data Explorer")
        de = cvde.gui.DataExplorer()
        de.run()

    elif sel_p == "Jobs":
        title("Jobs")
        jm = cvde.gui.Launcher()
        jm.run()

    elif sel_p == "Inspector":
        title("Inspector")
        jt = cvde.gui.JobInspector()
        jt.run()


if __name__ == "__main__":
    st.set_page_config(
        layout="wide",
        page_title=WS().name,
        menu_items={
            "Get Help": "https://github.com/LukasDb/CVDE",
            "Report a bug": "https://github.com/LukasDb/CVDE/issues",
            "About": "Tool to manage CV experiments and training deep learning models.",
        },
    )
    main()
