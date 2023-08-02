import streamlit as st
import streamlit_scrollable_textbox as stx
from streamlit_tags import st_tags, st_tags_sidebar
import os
import yaml
import numpy as np
import plotly.graph_objects as go
from typing import List, Dict, Type, Set
import time
from PIL import Image

from cvde.job.job_tracker import JobTracker, LogEntry


class JobInspector:
    def __init__(self) -> None:
        self.expanders: Dict[str, Type] = {}
        self.expand_all = False

        self.runs = os.listdir("log")
        self.all_trackers = [JobTracker.from_log(run) for run in self.runs]
        self.all_trackers.sort(key=lambda t: t.started, reverse=True)

        if "tags" not in st.session_state:
            st.session_state.tags = set()

        self.tags: Set[str] = st.session_state.tags
        self.tags.clear()
        for t in self.all_trackers:
            for tag in t.tags:
                self.tags.add(tag)

        st.subheader("Runs", anchor=False)

    def run(self):
        trackers = self.get_selected_trackers()  # also builds the sidebar
        trackers.sort(key=lambda t: t.started, reverse=True)

        # extract variable names
        var_names = []
        [var_names.extend(t.vars) for t in trackers]
        var_names = np.unique(var_names)

        if len(trackers) > 0:
            try:
                num_epochs = list([len(x.read_var(x.vars[0])) for x in trackers])
            except Exception:
                num_epochs = [0]
            self.max_epoch = max(num_epochs)

            cols = st.columns(len(trackers))
            for tracker, col in zip(trackers, cols):
                with col:
                    tags = st_tags(
                        value=tracker.tags,
                        label="Tags",
                        suggestions=list(self.tags),
                        key="tags_" + tracker.unique_name,
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
                    if self.max_epoch > 1:
                        epoch = exp.slider(
                            "select",
                            min_value=0,
                            label_visibility="hidden",
                            max_value=self.max_epoch - 1,
                            key="epch_slider" + var_name + t.unique_name,
                            value=self.max_epoch - 1,
                        )
                    else:
                        epoch = 0
                    img_path = y[epoch]
                    # read img
                    img = Image.open(img_path)

                    exp.image(img, caption=f"{t.display_name}")

                else:
                    if fig is None:
                        fig = go.Figure()

                    fig.add_scatter(x=x, y=y, name=t.display_name, showlegend=True)
                    exp = self.get_expander(var_name, default=st.empty)
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

    def get_selected_trackers(self) -> List[JobTracker]:
        # assemble settings in sidebar
        with st.sidebar:
            st.subheader("Settings")
            self.use_time = st.checkbox("Use actual time")
            self.log_axes = st.checkbox("Logarithmic", value=True)
            self.expand_all = st.checkbox("Expand all")
            selected_tags = st.multiselect("Filter by tags", options=self.tags)
            cols = st.columns(2)
            cols[0].subheader("Logged runs", anchor=False)
            all_selected = cols[1].checkbox("Select all")

        # filter by tags
        if len(selected_tags) > 0:
            self.all_trackers = [
                t for t in self.all_trackers if any(tag in selected_tags for tag in t.tags)
            ]

        # gui + select runs
        trackers: List[JobTracker] = []
        for tracker in self.all_trackers:
            with st.sidebar:
                if st.checkbox(tracker.display_name, value=all_selected, key=tracker.unique_name):
                    trackers.append(tracker)

        with st.sidebar:
            [st.text("") for i in range(10)]
            delete_button = st.empty()
            clicked_delete = delete_button.button("Delete selected")
            if clicked_delete:
                delete_button.button("Confirm?", key="confirm_delete_jobs")

            if st.session_state.get("confirm_delete_jobs", False):
                for t in trackers:
                    if t.in_progress:
                        st.error(f"Can't delete running job {t.name}")
                    else:
                        t.delete_log()
                time.sleep(0.5)
                st.experimental_rerun()
        return trackers

    def get_expander(self, var_name, default=None):
        if var_name not in self.expanders:
            self.expanders[var_name] = exp = st.expander(var_name, expanded=self.expand_all)

            if default is not None:
                with exp:
                    container = default()
                # overwrite to internal container
                self.expanders[var_name] = container

        return self.expanders[var_name]
