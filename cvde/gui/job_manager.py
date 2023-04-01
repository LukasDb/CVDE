from cvde.workspace import Workspace as WS
from cvde.workspace import ModuleExistsError
from cvde.job_handler import execute_job
import streamlit as st
import pandas as pd
import threading


class JobManager:
    def __init__(self) -> None:
        self.jobs = WS().jobs
        self.managed = {'Task':WS().tasks,
                        'Config':WS().configs,
                        'Model':WS().models,
                        'Train Dataset':WS().datasets,
                        'Val Dataset':WS().datasets}

        for v in self.managed.values():
            v.append('None')


    def run(self):
        st.title("Job Manager")
        buttons = st.columns(4)
        buttons[0].button("Add Job", on_click=self.add_empty_job)
        buttons[1].button("Duplicate Selected", on_click=self.duplicate_selected)
        buttons[2].button("Delete Selected", on_click=self.delete_jobs)
        buttons[3].button("Launch Selected", on_click=self.run_job)


        rows, = st.columns(1)
        with rows:
            for name, job_config in self.jobs.items():
                self.gui_row_from_job(name, job_config)

    def run_job(self):
        for name, job in self.jobs.items():
            if st.session_state[name+'selected']:
                args = (job['Task'], job['Config'], job['Model'], job['Train Dataset'], job['Val Dataset'])
                t = threading.Thread(target=execute_job, args=args, daemon=True)
                t.start()
        self.unselect_all()


    def gui_row_from_job(self, name, job_config):
        cols = st.columns(7)

        # TODO add multiselect for gpu

        if name+'selected' not in st.session_state:
            st.session_state[name+'selected'] = False
        
        cols[0].checkbox("Select job", key=name+'selected', label_visibility="hidden")
        cols[1].text_input("Job", value=name, key=name+'name', on_change=self.change_name, args=(name,))

        def selectbox_for_type(handle, key):
            options = self.managed[key]
            default_chosen = job_config[key]

            st.session_state[name+'__'+key] = default_chosen
            handle.selectbox(key, options, key=name+'__'+key, on_change=self.update_config, args=(name,key))
        
        selectbox_for_type(cols[2], 'Task')
        selectbox_for_type(cols[3], 'Config')
        selectbox_for_type(cols[4], 'Model')
        selectbox_for_type(cols[5], 'Train Dataset')
        selectbox_for_type(cols[6], 'Val Dataset')

    def unselect_all(self):
        for job in self.jobs:
            st.session_state[job+'selected'] = False

    def delete_jobs(self):
        for job in self.jobs:
            if st.session_state[job+'selected']:
                self.delete_job(job)
        self.unselect_all()

    def delete_job(self, job_name):
        WS().delete('jobs', job_name)

    def update_config(self, name, type):
        new_job_config = self.jobs[name]
        val = st.session_state[name+'__'+type]
        new_job_config[type] = val
        self.delete_job(name)
        WS().new('jobs', name, job=new_job_config)

    def change_name(self, name):
        job = self.jobs[name]
        new_name = st.session_state[name+'name']
        try:
            WS().new('jobs', new_name, job=job)
            self.delete_job(name)
        except ModuleExistsError:
            st.error("Job already exists! Rename previous copy to a unique name.")

    def duplicate_selected(self):
        print(st.session_state)

        for job in self.jobs:
            if not st.session_state[job+'selected']:
                continue

            try:
                WS().new('jobs', job+'_copy', job=self.jobs[job])
            except ModuleExistsError:
                st.error("Job already exists! Rename previous copy to a unique name.")
        self.unselect_all()
    
    def add_empty_job(self):
        empty_job = {'Task':'None', 'Model':'None', 'Config':'None', 'Model':'None', 'Train Dataset':'None', 'Val Dataset':'None'}
        WS().new('jobs', 'New Job', job=empty_job)

