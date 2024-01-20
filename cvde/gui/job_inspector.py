import streamlit as st
from streamlit.delta_generator import DeltaGenerator
import streamlit_scrollable_textbox as stx  # type: ignore
from streamlit_tags import st_tags  # type: ignore
import os
import yaml
import numpy as np
import plotly.graph_objects as go  # type: ignore
import time

from cvde.job.run_logger import RunLogger, LogEntry
from .page import Page


class JobInspector(Page):
    def __init__(self) -> None:
        if "tags" not in st.session_state:
            st.session_state.tags = set()

    def run(self) -> None:
        self.expanders: dict[str, DeltaGenerator] = {}
        self.expand_all = False
        self.runs = os.listdir("log")
        all_logs = [RunLogger.from_log(run) for run in self.runs]
        all_logs.sort(key=lambda t: t.started, reverse=True)

        tags = st.session_state.tags  # shorthand

        for log in all_logs:
            for tag in log.tags:
                tags.add(tag)

        with st.sidebar:
            st.subheader("Settings")
            self.use_time = st.checkbox("Use actual time")
            self.log_axes = st.checkbox("Logarithmic", value=True)
            self.expand_all = st.checkbox("Expand all")
            selected_tags = st.multiselect("Filter by tags", options=tags)
            cols = st.columns(2)
            cols[0].subheader("Logged runs", anchor=False)
            all_selected = cols[1].checkbox(
                "Select all", on_change=self.select_all, key="select_all"
            )

        selected_logs: list[RunLogger] = []
        for log in all_logs:
            has_a_selected_tag = any(tag in selected_tags for tag in log.tags)
            if len(selected_tags) > 0 and not has_a_selected_tag:
                continue

            if st.sidebar.checkbox(
                log.display_name, value=all_selected, key="select_" + log.folder_name
            ):
                selected_logs.append(log)

        with st.sidebar:
            [st.text("") for i in range(10)]  # vertical spacing
            delete_button = st.empty()
            clicked_delete = delete_button.button("Delete selected")
            if clicked_delete:
                delete_button.button("Confirm?", key="confirm_delete_jobs")

            if st.session_state.get("confirm_delete_jobs", False):
                for log in selected_logs:
                    if log.is_in_progress():
                        st.error(f"Can't delete running job {log.name}")
                    else:
                        log.delete_log()
                time.sleep(0.5)
                st.rerun()

        st.subheader("Runs", anchor=False)

        # extract variable names
        var_names = np.unique([var_name for log in selected_logs for var_name in log.vars])

        if len(selected_logs) > 0:
            cols = st.columns(len(selected_logs))
            for log, column in zip(selected_logs, cols):
                with column:
                    added_tags = st_tags(
                        value=log.tags,
                        label=f"{log.display_name}",
                        suggestions=list(tags),
                        key="tags_" + log.folder_name,
                        text="Add tags...",
                    )
                    for tag in added_tags:
                        tags.add(tag)
                    log.set_tags(added_tags)

        # display data
        # for each variable name, assemble plot of data
        for var_name in var_names:
            fig = None
            for log in selected_logs:
                try:
                    run_data = log.read_var(var_name)
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
                            key="num_epoch_" + var_name + log.folder_name,
                        )
                    else:
                        epoch = 0
                    img_path = y[epoch]
                    # read img
                    # img = Image.open(img_path)

                    exp.image(img_path, caption=f"{log.display_name}")

                else:
                    if fig is None:
                        fig = go.Figure()

                    fig.add_scatter(x=x, y=y, name=log.display_name, showlegend=True)
                    exp = self.get_expander(var_name, create_empty=True)
                    if self.log_axes:
                        fig.update_yaxes(type="log")
                    fig.update_layout(legend=dict(orientation="h"))
                    exp.plotly_chart(fig)

        conf_exp = st.expander("Config")
        if len(selected_logs) == 0:
            return
        cols = conf_exp.columns(len(selected_logs))

        for column, log in zip(cols, selected_logs):
            column.text(f"{log.name} ({log.started})")
            column.code(yaml.dump(log.config), language="yaml")

        stdout_exp = st.expander("Stdout")
        cols = stdout_exp.columns(len(selected_logs))
        for log, column in zip(selected_logs, cols):
            column.text(f"{log.name} ({log.started})")
            with column:
                stx.scrollableTextbox(
                    log.get_stdout(),
                    height=400,
                    fontFamily="monospace",
                    key=log.folder_name + "_stdout",
                )

        stderr_exp = st.expander("Stderr")
        cols = stderr_exp.columns(len(selected_logs))
        for log, column in zip(selected_logs, cols):
            column.text(f"{log.name} ({log.started})")
            with column:
                stx.scrollableTextbox(
                    log.get_stderr(),
                    height=400,
                    fontFamily="monospace",
                    key=log.folder_name + "_stderr",
                )

    def on_leave(self) -> None:
        return super().on_leave()

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
