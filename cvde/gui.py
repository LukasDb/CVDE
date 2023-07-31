import sys
import os

import silence_tensorflow.auto
import tensorflow as tf
import itertools as it

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
import threading
from pathlib import Path
import colorama


def main():
    sys.path.append(os.getcwd())

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
        c2.markdown(f'{current_weather} *Last update: {datetime.now().strftime("%H:%M:%S")}*')

    sel_p = st.session_state["selected_page"]
    if sel_p == "Dashboard":
        title("Dashboard")
        from cvde.gui.dashboard import dashboard

        dashboard()

    elif sel_p == "Data":
        title("Data Explorer")
        from cvde.gui.data_explorer import data_explorer

        data_explorer()

    elif sel_p == "Models":
        title("Model Explorer")
        from cvde.gui.model_explorer import ModelExplorer

        me = ModelExplorer()
        me.run()

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

    class ThreadPrinter:
        def __init__(self, stream):
            self.file_outs = {}
            self.colors = {}
            self.stream = stream
            self.main_thread = threading.currentThread()
            self._lock = threading.Lock()
            self._colors = it.cycle(
                [
                    colorama.Fore.RED,
                    colorama.Fore.GREEN,
                    colorama.Fore.YELLOW,
                    colorama.Fore.BLUE,
                    colorama.Fore.MAGENTA,
                    colorama.Fore.CYAN,
                ]
            )

        def register_new_out(self, filepath: Path):
            with self._lock:
                cur = threading.currentThread()
                self.file_outs[cur] = filepath.open('w')
                self.colors[cur] = next(self._colors)

        def write(self, value):
            with self._lock:
                try:
                    color = self.colors[threading.currentThread()]
                except KeyError:
                    color = colorama.Fore.WHITE

                self.stream.write(color + value)
                try:
                    file = self.file_outs[threading.currentThread()]
                    file.write(value)
                except KeyError:
                    pass
            self.flush()

        def flush(self):
            with self._lock:
                self.stream.flush()
                try:
                    file = self.file_outs[threading.currentThread()]
                    file.flush()
                except KeyError:
                    return

    sys.stdout = ThreadPrinter(sys.__stdout__)
    sys.stderr = ThreadPrinter(sys.__stderr__)
    main()
