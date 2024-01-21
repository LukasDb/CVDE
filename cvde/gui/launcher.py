import streamlit as st
import streamlit_ace as st_ace  # type: ignore
import pathlib
import datetime
import yaml
import cvde
from cvde.scheduler import Scheduler, JobSubmission
from .page import Page


class Launcher(Page):
    ace_options = {
        "language": "yaml",
        "show_gutter": False,
        "auto_update": True,
        "theme": "tomorrow_night",
        "min_lines": 5,
        "tab_size": 2,
    }

    def __init__(self) -> None:
        if "last_submitted" not in st.session_state:
            st.session_state.last_submitted = None

    def run(self) -> None:
        st.warning(
            "Work in Progress: When you submit a job, the current configuration will be used when the job is launched. However, the current state of the code is not! At the time of the launch of the job (which is not necessarily the time you submit it), the code will be imported by Python."
        )
        st.subheader("Job Queue")
        scheduler: Scheduler = st.session_state["scheduler"]
        st.graphviz_chart(scheduler.get_digraph())

        self.configs = cvde.Workspace().list_configs()

        with st.sidebar:
            with st.form(clear_on_submit=True, key="add_tag_form", border=True):
                new_tag = st.text_input("Add new tags")
                st.form_submit_button(
                    "Add new tag",
                )

        with st.sidebar.container(border=True):
            st.subheader("Submit Job")

            # choose job
            job_names = list(cvde.Workspace().list_jobs().keys())
            job_name = st.selectbox("Job", job_names)
            assert isinstance(job_name, str)

            # choose config
            config_name = st.selectbox("Config", list(self.configs.keys()))
            assert isinstance(config_name, str)
            now = datetime.datetime.now().strftime("%Y%m%d_%H%M")
            default_run_name = f"{now}_{job_name}_{config_name}"

            # choose environment variables
            env_string = st.text_input(
                "Environment Variables",
                value="CUDA_VISIBLE_DEVICES=0",
                help="Set environment variables and separate with semicolons.",
            )
            env = {
                key.strip(): value.strip()
                for key, value in [word.split("=") for word in env_string.split(";")]
            }

            # choose run name
            run_name = st.text_input(
                "Run Name",
                value=default_run_name,
                help="To help distinguish runs with similar configs, you can give your experiment a custom name.",
            )
            if len(run_name) == 0:
                run_name = default_run_name

            default_tag = None
            if len(new_tag) > 0:
                st.session_state.tags.add(new_tag)
                default_tag = new_tag

            tags = st.multiselect(
                "Choose Tags", list(st.session_state.tags), key="choose_tags", default=default_tag
            )

            options = scheduler.get_scheduled_submissions()
            default = (
                st.session_state.last_submitted
                if st.session_state.last_submitted in options
                else None
            )
            after = st.multiselect(
                "Wait for job",
                default=default,
                options=options,
                format_func=lambda x: x.run_name,
                key="wait_for_job",
                help="Choose jobs to wait for before starting this one. Otherwise the job will be launched immediately and parallel to other jobs.",
            )

            submit = st.button("Submit", use_container_width=True, type="primary")

        if config_name is None:
            return

        # load file directly to preserve comments
        config_path = pathlib.Path("configs/" + config_name + ".yml")
        with config_path.open() as F:
            config_text = F.read()

        st.subheader(f"Config Editor: {config_name}")
        new_config_text = st_ace.st_ace(config_text, **self.ace_options, key="ace_" + config_name)
        if new_config_text != config_text:
            with config_path.open("w") as F:
                F.write(new_config_text)

        config = yaml.load(new_config_text, Loader=yaml.Loader)

        if submit:
            submission = JobSubmission(
                config=config,
                job_name=job_name,
                run_name=run_name,
                tags=tags,
                env=env,
            )
            st.session_state.last_submitted = submission

            scheduler.submit(submission, after)
            cvde.gui.notify(f"{run_name} submitted.")
            st.rerun()

    def on_leave(self) -> None:
        return super().on_leave()
