import pandas as pd
from workspace_tools import load_config, write_config
from workspace import Workspace as WS
import streamlit as st
import streamlit_ace as st_ace
import yaml
import pathlib

class ConfigEditor():
    ace_options = {
        'language':'yaml',
        'show_gutter':False,
        'auto_update':False,
        'theme':'tomorrow_night',
        'min_lines':5
        }


    def run(self):
        cfg_name = st.selectbox("Configuration", options=WS().configs)
        #config = load_config(cfg_name)
        #modified = {}
        #for key, conf in config.items():
        #    st.subheader(f"Kwargs ({key})", anchor=False)
        #config_read = yaml.dump(config, line_break=True)
        cfg_path = pathlib.Path('configs/'+ cfg_name + '.yml')
        with cfg_path.open() as F:
            cfg = F.read()

        text = st_ace.st_ace(cfg, **self.ace_options)
        #modified = yaml.safe_load(text)

        with cfg_path.open('w') as F:
            F.write(text)
        
        #write_config(cfg_name, modified)
        

