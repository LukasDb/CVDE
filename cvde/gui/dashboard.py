import time
import os
import itertools as it
import streamlit as st
import cvde
from .page import Page
import multiprocessing as mp


class Dashboard(Page):
    def __init__(self) -> None:
        pass

    def run(self) -> None:
        log_folders = os.listdir("log")
        all_logs = [cvde.job.RunLogger.from_log(folder) for folder in log_folders]
        running_logs = [l for l in all_logs if l.is_in_progress()]

        with st.expander("Runs", expanded=True):
            cols = it.cycle(st.columns(2))

            for log in running_logs:
                with next(cols) as c:
                    c1, c2 = st.columns(2)
                    c2.markdown(f"**{log.display_name}**")

                    kill_button = c1.empty()
                    clicked_kill = kill_button.button("Stop", key="kill_job_" + log.name)
                    if clicked_kill:
                        kill_button.button("Confirm?", key="confirm_kill_job_" + log.name)

                    if st.session_state.get("confirm_kill_job_" + log.name, False):
                        cvde.gui.warn(f"Stopping {log.display_name}...")
                        process = log.get_mp_process()
                        process.terminate()

                        time.sleep(1.0)
                        st.rerun()

                    try:
                        stdout = "\n".join(log.get_stdout().strip().split("\n")[-1:])
                        st.text("stdout")
                        st.code(stdout, language="html")
                    except Exception:
                        pass

                    try:
                        stderr = "\n".join(log.get_stderr().strip().split("\n")[-1:])
                        st.text("stderr")
                        st.code(stderr, language="html")
                    except Exception:
                        pass

                    st.divider()

        with st.expander("Device Status", expanded=True):
            if "nv_smi_available" not in st.session_state:
                st.session_state["nv_smi_available"] = (
                    os.system("which nvidia-smi > /dev/null") == 0
                )

            if not st.session_state["nv_smi_available"]:
                return
            os.system("nvidia-smi > /tmp/gpu_util.txt")

            with open("/tmp/gpu_util.txt", "r") as f:
                gpu_util = f.read()
            st.code(gpu_util, language="html")

    def on_leave(self) -> None:
        return super().on_leave()
