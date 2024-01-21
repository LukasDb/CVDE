import sys
import os

import streamlit as st
from datetime import datetime
import cvde
from gui.page import Page
import requests

from cvde.scheduler import Scheduler


@st.cache_resource
def get_scheduler() -> Scheduler:
    return Scheduler()


class GUI:
    def __init__(self) -> None:
        sys.path.append(os.getcwd())

        # create persistent job scheduler
        st.session_state["scheduler"] = get_scheduler()

        # initialize tags
        if "tags" not in st.session_state:
            st.session_state.tags = set()
            runs = os.listdir("log")
            all_logs = [cvde.job.RunLogger.from_log(run) for run in runs]
            all_logs.sort(key=lambda t: t.started, reverse=True)
            for log in all_logs:
                print(f"adding tags from {log}: {log.tags}")
                st.session_state.tags.update({t for t in log.tags})

        style_file = os.path.join(os.path.dirname(__file__), "style.css")
        with open(style_file) as F:
            style = F.read()
        st.markdown(f"<style>{style}</style>", unsafe_allow_html=True)

        pages: dict[str, Page] = {
            "Dashboard": cvde.gui.Dashboard(),
            "Data": cvde.gui.DataExplorer(),
            "Launcher": cvde.gui.Launcher(),
            "Inspector": cvde.gui.JobInspector(),
        }

        if "selected_page" not in st.session_state:
            st.session_state["selected_page"] = "Dashboard"

        cols = st.columns(len(pages) + 1)
        cols[0].text("")
        cols[0].markdown(f"**{cvde.Workspace().name}**")

        for col, page_name in zip(cols[1:], pages.keys()):
            col.write("""<div class='PortMarker'/>""", unsafe_allow_html=True)
            if col.button(f"**{page_name}**", use_container_width=True):
                # chose a page
                last_page_name = st.session_state["selected_page"]
                if page_name != last_page_name:
                    pages[last_page_name].on_leave()
                st.session_state["selected_page"] = page_name

        active_page_name = st.session_state["selected_page"]

        self.title(active_page_name)
        pages[active_page_name].run()

    def title(self, t: str) -> None:
        if "weather" not in st.session_state:
            st.session_state["weather"] = ""

        if "last_weather_update" not in st.session_state:
            st.session_state["last_weather_update"] = datetime.now()

        if (datetime.now() - st.session_state["last_weather_update"]).seconds > 60:
            # update weather
            try:
                current_weather = requests.get(
                    "http://www.wttr.in", params={"format": "%c %t"}, timeout=0.5
                ).text
                st.session_state["last_weather_update"] = datetime.now()
            except Exception:
                current_weather = ""
            st.session_state["weather"] = current_weather

        current_weather = st.session_state["weather"]

        st.title(t, anchor=False)
        c1, c2 = st.columns([1, 20])
        c1.button("⟳", key=t + "_reload")
        c2.markdown(
            f'{current_weather} *Last update: {st.session_state["last_weather_update"].strftime("%H:%M:%S")}*'
        )


if __name__ == "__main__":
    st.set_page_config(
        layout="wide",
        page_title=cvde.Workspace().name,
        menu_items={
            "Get Help": "https://github.com/LukasDb/CVDE",
            "Report a bug": "https://github.com/LukasDb/CVDE/issues",
            "About": "Tool to manage CV experiments and training deep learning models.",
        },
    )
    GUI()
