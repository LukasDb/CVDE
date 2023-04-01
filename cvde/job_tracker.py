import pickle
import json
import streamlit as st
from datetime import datetime
from cvde.workspace_tools import load_config
import os
from dataclasses import dataclass


@dataclass
class JobTracker:
    name: str
    task: str
    config_name: str
    model: str
    train_set: str
    val_set: str
    config: dict
    
    def __post_init__(self):
        self.root = None
        self.folder_name = None
        self.started = None
        self.var_root = None
        self.in_progress = False
        self.index = 0

    @staticmethod
    def from_log(folder_name):
        with open(os.path.join('log',folder_name,'log.json')) as F:
            meta = json.load(F)

        tracker = JobTracker(meta['name'], None, None, None, None, None, meta['config'])
        tracker.folder_name = folder_name
        tracker.started = meta['started']
        tracker.root = os.path.join("log", tracker.folder_name)
        tracker.var_root = os.path.join(tracker.root, 'vars')
        return tracker
    
    @staticmethod
    def create(name:str, task: str, config_name: str, model: str, train_set: str, val_set: str):
        # use time as a unique key
        config = load_config(config_name)

        tracker = JobTracker(name, task, config_name, model, train_set, val_set, config)

        tracker.folder_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        tracker.root = os.path.join("log", tracker.folder_name)
        tracker.var_root = os.path.join(tracker.root, 'vars')
        os.makedirs(tracker.root)
        os.makedirs(tracker.var_root)
        tracker.meta = {
            "name": tracker.name,
            "started": None,
            "task": tracker.task,
            "model": tracker.model,
            "train Dataset": tracker.train_set,
            "val Dataset": tracker.val_set,
            "config": config,
            "in_progress": False
        }

        with open(os.path.join(tracker.root, 'log.json'), 'w') as F:
            json.dump(tracker.meta, F, indent=2)
        return tracker   
    
    def __enter__(self):
        self.in_progress = True
        with open(os.path.join(self.root, 'log.json'), 'r') as F:
            data = json.load(F)
        data["in_progress"] = True
        data["started"] = self.started = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
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