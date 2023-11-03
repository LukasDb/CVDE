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
        from cvde.gui.dashboard import dashboard

        dashboard()

    elif sel_p == "Data":
        title("Data Explorer")
        from cvde.gui.data_explorer import DataExplorer
        DataExplorer()

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

    class ThreadPrinter:
        def __init__(self, stream):
            self.file_outs = {}
            self.colors = {}
            self.stream = stream
            self.encoding = stream.encoding
            self._lock = threading.Lock()
            self._colors = [
                colorama.Fore.RED,
                colorama.Fore.GREEN,
                colorama.Fore.YELLOW,
                colorama.Fore.BLUE,
                colorama.Fore.MAGENTA,
                colorama.Fore.CYAN,
            ]
            self.last_color_i = 0

        def register_new_out(self, filepath: Path):
            with self._lock:
                cur = threading.currentThread().ident
                self.file_outs[cur] = filepath.open("w")
                self.colors[cur] = self._colors[self.last_color_i % len(self._colors)]
                self.last_color_i += 1

        def write(self, value):
            with self._lock:
                try:
                    color = self.colors[threading.currentThread().ident]
                except KeyError:
                    color = colorama.Fore.WHITE
                    

                self.stream.write(color)
                self.stream.flush()
                self.stream.write(value)
                self.stream.flush()
                try:
                    file = self.file_outs[threading.currentThread().ident]
                    file.write(value)
                    file.flush()
                except KeyError:
                    pass

        def __eq__(self, other):
            return other is self.stream

        def flush(self):
            with self._lock:
                try:
                    file = self.file_outs[threading.currentThread().ident]
                    file.flush()
                except KeyError:
                    return
                self.stream.flush()

    @st.cache_resource
    def get_stdout_threadprinter():
        return ThreadPrinter(sys.stdout)

    @st.cache_resource
    def get_stderr_threadprinter():
        return ThreadPrinter(sys.stderr)

    sys.stdout = get_stdout_threadprinter()
    sys.stderr = get_stderr_threadprinter()
    main()
