import streamlit as st
import streamlit_scrollable_textbox as stx
import os
import yaml
import numpy as np
import plotly.graph_objects as go
from typing import List
import time

from cvde.job.job_tracker import JobTracker, LogEntry


class JobInspector:
    TAGS = ["final", "notable", "testing"]

    def __init__(self) -> None:
        self.expanders = {}
        self.img_epochs = {}
        self.expand_all = False

        self.runs = os.listdir("log")
        self.all_trackers = [JobTracker.from_log(run) for run in self.runs]
        self.all_trackers.sort(key=lambda t: t.started, reverse=True)
        st.subheader("Runs", anchor=False)

    def run(self):
        trackers = self.get_selected_trackers() # also builds the sidebar
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

                # convert tensors to numpy
                if hasattr(y[0], "cpu"):
                    y = [i.cpu() for i in y]
                if hasattr(y[0], "detach"):
                    y = [i.detach() for i in y]
                if hasattr(y[0], "numpy"):
                    y = [i.numpy() for i in y]

                y = np.array(y)

                if len(y.shape) == 3:
                    # add channel to channel less images
                    y = np.expand_dims(y, -1)

                if len(y.shape) == 4:
                    self.visualize_image_with_controls(var_name, y, t.unique_name)

                elif len(y.shape) == 1:
                    if fig is None:
                        fig = go.Figure()

                    fig.add_scatter(x=x, y=y, name=t.unique_name, showlegend=True)
                    exp = self.get_expander(var_name, default=st.empty)
                    if self.log_axes:
                        fig.update_yaxes(type="log")
                    exp.plotly_chart(fig)

        conf_exp = st.expander("Config")
        if len(trackers) == 0:
            return
        cols = conf_exp.columns(len(trackers))
        for col, tracker in zip(cols, trackers):
            col.text(f"{tracker.name} ({tracker.started})")
            col.code(yaml.dump(tracker.config), language="yaml")

        tags_exp = st.expander("Set tags")
        cols = tags_exp.columns(len(trackers))
        for tracker, col in zip(trackers, cols):
            set_tags = col.multiselect(
                f"Tags: {tracker.name}", self.TAGS, default=tracker.tags, key="tags_"+tracker.unique_name
            )
            tracker.set_tags(set_tags)

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

    def get_selected_trackers(self):
        # assemble settings in sidebar
        with st.sidebar:
            st.subheader("Settings")
            self.use_time = st.checkbox("Use actual time")
            self.log_axes = st.checkbox("Logarithmic", value=True)
            self.expand_all = st.checkbox("Expand all")
            selected_tags = st.multiselect("Filter by tags", options=self.TAGS)
            cols = st.columns(2)
            cols[0].subheader("Logged runs", anchor=False)
            all_selected = cols[1].checkbox("Select all")

        # filter by tags
        if len(selected_tags) > 0:
            self.all_trackers = [
                t
                for t in self.all_trackers
                if any(tag in selected_tags for tag in t.tags)
            ]

        # gui + select runs
        trackers: List[JobTracker] = []
        for tracker in self.all_trackers:
            with st.sidebar:
                if st.checkbox(
                    tracker.display_name, value=all_selected, key=tracker.unique_name
                ):
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
            self.expanders[var_name] = exp = st.expander(var_name,expanded=self.expand_all)

            if default is not None:
                with exp:
                    container = default()
                # overwrite to internal container
                self.expanders[var_name] = container

        return self.expanders[var_name]

    def visualize_image_with_controls(self, var_name, imgs, caption):
        exp = self.get_expander(var_name)

        if var_name not in self.img_epochs:
            epoch = 0
            if self.max_epoch > 1:
                epoch = exp.slider(
                    "select",
                    min_value=0,
                    label_visibility="hidden",
                    max_value=self.max_epoch - 1,
                    key=var_name,
                    value=self.max_epoch - 1,
                )

            self.img_epochs[var_name] = epoch

        try:
            epoch = self.img_epochs[var_name]
            img = imgs[epoch]
        except Exception:
            exp.error(f"Not enough datapoints {caption}")
            return

        channel_dim = np.argmin(img.shape)
        other_dims = [i for i in range(3) if i != channel_dim]
        transp = [*other_dims, channel_dim]
        img = np.transpose(img, transp)

        exp.image(img, caption=caption)
