import streamlit as st
import streamlit_ace as st_ace  # type: ignore
import pathlib
import datetime
import yaml
import cvde
from .page import Page
import wonderwords


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
        if not cvde.Workspace().git_tracking_enabled:
            st.warning(
                "Git Tracking is not enabled! This means, the code at job submit time might be different from the code when the job is actually launched. Git Tracking saves a snapshot of your code at submission time and checks out to it when launching the job. To enable Git Tracking, run `cvde init` in your workspace directory."
            )
        st.subheader("Job Queue")
        scheduler: cvde.Scheduler = st.session_state["scheduler"]
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
            index = (
                0
                if st.session_state.get("launcher_job_select", None) is None
                else job_names.index(st.session_state["launcher_job_select"])
            )
            st.markdown("Job")
            job_name = st.selectbox("Job", job_names, index=index, label_visibility="collapsed")
            st.session_state["launcher_job_select"] = job_name

            assert isinstance(job_name, str)

            # choose config
            configs = list(self.configs.keys())
            index = (
                0
                if st.session_state.get("launcher_config_select", None) is None
                else configs.index(st.session_state["launcher_config_select"])
            )
            st.markdown("Config")
            config_name = st.selectbox("Config", configs, index=index, label_visibility="collapsed")
            assert isinstance(config_name, str)
            st.session_state["launcher_config_select"] = config_name

            # choose environment variables
            st.markdown("Environment Variables")
            env_string = st.text_input(
                "Environment Variables",
                value=st.session_state.get("launcher_env_string", "CUDA_VISIBLE_DEVICES=0"),
                help="Set environment variables and separate with semicolons.",
                label_visibility="collapsed",
            )
            st.session_state["launcher_env_string"] = env_string

            env = {
                key.strip(): value.strip()
                for key, value in [word.split("=") for word in env_string.split(";")]
            }

            # choose run name
            # now = datetime.datetime.now().strftime("%Y%m%d_%H%M")
            # default_run_name = f"{now}_{job_name}_{config_name}"

            st.markdown("Run name")
            c1, c2 = st.columns([3, 1])
            if c2.button("🔄") or "launcher_run_name" not in st.session_state:
                r = wonderwords.RandomWord()
                word1 = r.word(
                    include_parts_of_speech=["adjectives"], word_min_length=4, word_max_length=8
                )
                word2 = r.word(
                    include_parts_of_speech=["nouns"], word_min_length=4, word_max_length=8
                )
                st.session_state["launcher_run_name"] = f"{word1}_{word2}"

            run_name = c1.text_input(
                "Run Name",
                value=st.session_state.get("launcher_run_name", ""),
                label_visibility="collapsed",
                # help="To help distinguish runs with similar configs, you can give your experiment a custom name.",
            )
            st.session_state["launcher_run_name"] = run_name

            run_name = run_name.replace(" ", "_")
            run_name = run_name.replace(".", "_")
            run_name = run_name.replace("/", "_")
            run_name = run_name.replace("\\", "_")
            run_name = run_name.replace(":", "_")
            run_name = run_name.replace(";", "_")
            run_name = run_name.replace(",", "_")

            default_tag = None
            if len(new_tag) > 0:
                st.session_state.tags.add(new_tag)
                default_tag = new_tag

            tags = st.multiselect(
                "Choose Tags", list(st.session_state.tags), key="choose_tags", default=default_tag
            )

            options = scheduler.get_scheduled_submissions()

            after = st.multiselect(
                "Wait for job",
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

        try:
            config = yaml.load(new_config_text, Loader=yaml.Loader)
        except Exception as e:
            st.error("Error parsing config file.")
            return

        if submit:
            submission = cvde.job.JobSubmission(
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
