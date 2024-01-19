import streamlit as st
from streamlit.delta_generator import DeltaGenerator
import streamlit_scrollable_textbox as stx  # type: ignore
from streamlit_tags import st_tags  # type: ignore
import os
import yaml
import numpy as np
import plotly.graph_objects as go  # type: ignore
from typing import Type
import time
from PIL import Image

from cvde.job.job_tracker import JobTracker, LogEntry


class JobInspector:
    def __init__(self) -> None:
        self.expanders: dict[str, DeltaGenerator] = {}
        self.expand_all = False
        self.runs = os.listdir("log")
        all_trackers = [JobTracker.from_log(run) for run in self.runs]
        all_trackers.sort(key=lambda t: t.started, reverse=True)

        if "tags" not in st.session_state:
            st.session_state.tags = set()
        self.tags: set[str] = st.session_state.tags
        self.tags.clear()
        for t in all_trackers:
            for tag in t.tags:
                self.tags.add(tag)

        with st.sidebar:
            st.subheader("Settings")
            self.use_time = st.checkbox("Use actual time")
            self.log_axes = st.checkbox("Logarithmic", value=True)
            self.expand_all = st.checkbox("Expand all")
            selected_tags = st.multiselect("Filter by tags", options=self.tags)
            cols = st.columns(2)
            cols[0].subheader("Logged runs", anchor=False)
            all_selected = cols[1].checkbox(
                "Select all", on_change=self.select_all, key="select_all"
            )

        self.active_trackers: list[JobTracker] = []
        for t in all_trackers:
            has_a_selected_tag = any(tag in selected_tags for tag in t.tags)
            if len(selected_tags) > 0 and not has_a_selected_tag:
                continue
            if st.sidebar.checkbox(
                t.display_name, value=all_selected, key="select_" + t.unique_name
            ):
                self.active_trackers.append(t)

        with st.sidebar:
            [st.text("") for i in range(10)]  # vertical spacing
            delete_button = st.empty()
            clicked_delete = delete_button.button("Delete selected")
            if clicked_delete:
                delete_button.button("Confirm?", key="confirm_delete_jobs")

            if st.session_state.get("confirm_delete_jobs", False):
                for t in self.active_trackers:
                    if t.in_progress:
                        st.error(f"Can't delete running job {t.name}")
                    else:
                        t.delete_log()
                time.sleep(0.5)
                st.experimental_rerun()

        st.subheader("Runs", anchor=False)

    def run(self) -> None:
        # trackers = self.get_selected_trackers()  # also builds the sidebar
        trackers = self.active_trackers
        trackers.sort(key=lambda t: t.started, reverse=True)

        # extract variable names
        var_names = []
        for t in trackers:
            var_names.extend(t.vars)
        var_names = np.unique(var_names)

        if len(trackers) > 0:
            cols = st.columns(len(trackers))
            for tracker, col in zip(trackers, cols):
                with col:
                    tags = st_tags(
                        value=tracker.tags,
                        label=f"{tracker.display_name}",
                        suggestions=list(self.tags),
                        key="tags_" + tracker.unique_name,
                        text="Add tags...",
                    )
                    for tag in tags:
                        self.tags.add(tag)
                    tracker.set_tags(tags)

        # display data
        # for each variable name, assemble plot of data
        for var_name in var_names:
            fig = None
            for t in trackers:
                try:
                    run_data = t.read_var(var_name)
                except FileNotFoundError:
                    continue

                key = "t" if self.use_time else "index"
                x = np.array([getattr(i, key) for i in run_data])
                y = [i.data for i in run_data]

                if len(y) == 0:
                    continue

                # convert tensors to numpy
                if hasattr(y[0], "cpu"):
                    y = [i.cpu() for i in y]
                if hasattr(y[0], "detach"):
                    y = [i.detach() for i in y]
                if hasattr(y[0], "numpy"):
                    y = [i.numpy() for i in y]

                if run_data[0].is_image:
                    exp = self.get_expander(var_name)
                    # select index
                    if len(y) > 1:
                        epoch = exp.slider(
                            "Select",
                            min_value=0,
                            label_visibility="hidden",
                            max_value=len(y) - 1,
                            value=len(y) - 1,
                            key="num_epoch_" + var_name + t.unique_name,
                        )
                    else:
                        epoch = 0
                    img_path = y[epoch]
                    # read img
                    # img = Image.open(img_path)

                    exp.image(img_path, caption=f"{t.display_name}")

                else:
                    if fig is None:
                        fig = go.Figure()

                    fig.add_scatter(x=x, y=y, name=t.display_name, showlegend=True)
                    exp = self.get_expander(var_name, create_empty=True)
                    if self.log_axes:
                        fig.update_yaxes(type="log")
                    fig.update_layout(legend=dict(orientation="h"))
                    exp.plotly_chart(fig)

        conf_exp = st.expander("Config")
        if len(trackers) == 0:
            return
        cols = conf_exp.columns(len(trackers))
        for col, tracker in zip(cols, trackers):
            col.text(f"{tracker.name} ({tracker.started})")
            col.code(yaml.dump(tracker.config), language="yaml")

        stdout_exp = st.expander("Stdout")
        cols = stdout_exp.columns(len(trackers))
        for tracker, col in zip(trackers, cols):
            col.text(f"{tracker.name} ({tracker.started})")
            with col:
                stx.scrollableTextbox(
                    tracker.get_stdout(),
                    height=400,
                    fontFamily="monospace",
                    key=tracker.unique_name + "_stdout",
                )

        stderr_exp = st.expander("Stderr")
        cols = stderr_exp.columns(len(trackers))
        for tracker, col in zip(trackers, cols):
            col.text(f"{tracker.name} ({tracker.started})")
            with col:
                stx.scrollableTextbox(
                    tracker.get_stderr(),
                    height=400,
                    fontFamily="monospace",
                    key=tracker.unique_name + "_stderr",
                )

    def get_expander(self, var_name: str, create_empty: bool = False) -> DeltaGenerator:
        if var_name not in self.expanders:
            self.expanders[var_name] = exp = st.expander(var_name, expanded=self.expand_all)

            if create_empty:
                with exp:
                    container = st.empty()
                # overwrite to internal container
                self.expanders[var_name] = container

        return self.expanders[var_name]

    def select_all(self) -> None:
        for key in st.session_state.keys():
            if isinstance(key, str) and key.startswith("select_"):
                st.session_state[key] = st.session_state["select_all"]
