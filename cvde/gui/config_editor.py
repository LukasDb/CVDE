import pandas as pd
from workspace_tools import load_config, write_config
from workspace import Workspace as WS
import streamlit as st
import streamlit_ace as st_ace
import yaml

class ConfigEditor():
    ace_options = {
        'language':'yaml',
        'show_gutter':False,
        'auto_update':False,
        'theme':'tomorrow_night',
        'min_lines':5
        }


    def run(self):
        st.title("Config Editor")
        cfg_name = st.selectbox("Configuration", options=WS().configs)
        config = load_config(cfg_name)
        modified = {}
        for key, conf in config.items():
            st.subheader(f"Kwargs for {key}")
            text = st_ace.st_ace(yaml.dump(conf),**self.ace_options)
            modified[key] = yaml.safe_load(text)
        
        write_config(cfg_name, modified)
        

