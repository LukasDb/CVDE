import pickle
import json
import streamlit as st
from datetime import datetime
from cvde.workspace_tools import load_config
import os
from dataclasses import dataclass

@dataclass
class JobConfig:
    name: str
    task: str
    config_name: str
    model: str
    train_set: str
    val_set: str


class JobTracker:
    def __init__(self, name:str, task: str, config_name: str, model: str, train_set: str, val_set: str):
        self.in_progress = False
        self.index = 0
        self.configuration = JobConfig(name, task, config_name, model, train_set, val_set)

    @staticmethod
    def from_log(folder_name):
        with open(os.path.join('log',folder_name,'log.json')) as F:
            meta = json.load(F)
        tracker = JobTracker(meta['name'], None, None, None, None, None)
        tracker.folder_name = folder_name
        tracker.root = os.path.join("log", tracker.folder_name)
        tracker.var_root = os.path.join(tracker.root, 'vars')
        return tracker
    
    def __enter__(self):
        self.in_progress = True
        with open(os.path.join(self.root, 'log.json'), 'r') as F:
            data = json.load(F)
        data["in_progress"]=True
        with open(os.path.join(self.root, 'log.json'), 'w') as F:
            json.dump(data, F, indent=2)

    def __exit__(self, type, value, traceback):
        self.in_progress = False
        with open(os.path.join(self.root, 'log.json'), 'r') as F:
            data = json.load(F)
        data["in_progress"]=False
        with open(os.path.join(self.root, 'log.json'), 'w') as F:
            json.dump(data, F, indent=2)
    
    @property
    def vars(self):
        return [x.split('.pkl')[0] for x in os.listdir(self.var_root)]
    
    def read_var(self, var):
        var_path = os.path.join(self.var_root, var+'.pkl')
        with open(var_path, 'rb') as F:
            data = pickle.load(F)
        return data

    def create(self):
        self.folder_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.root = os.path.join("log", self.folder_name)
        self.var_root = os.path.join(self.root, 'vars')
        os.makedirs(self.root)
        os.makedirs(self.var_root)
        config = load_config(self.configuration.config_name)
        self.meta = {
            "name": self.configuration.name,
            "started": self.folder_name,
            "task": self.configuration.task,
            "model": self.configuration.model,
            "train Dataset": self.configuration.train_set,
            "val Dataset": self.configuration.val_set,
            "configuration": config,
            "in_progress": False
        }

        with open(os.path.join(self.root, 'log.json'), 'w') as F:
            json.dump(self.meta, F, indent=2)

    
    def log(self, name, var):
        """ log variable """
        var_path = os.path.join(self.var_root, name+'.pkl')
        try:
            with open(var_path, 'rb') as F:
                data = pickle.load(F)
        except FileNotFoundError:
            data = []

        new_data = {
            't':datetime.now(),
            'data': var,
            'index': len(data)
        }
        data.append(new_data)

        with open(var_path, 'wb') as F:
            pickle.dump(data, F)