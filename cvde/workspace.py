import json
import yaml
import os
import logging
import importlib
from cvde.templates import realize_template

import sys
sys.path.append(os.getcwd())


class ModuleExistsError(Exception):
    pass

class Workspace:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Workspace, cls).__new__(
                cls, *args, **kwargs)
        return cls._instance
    
    @property
    def _state(self):
        with open(".workspace.cvde") as F:
            ws = json.load(F)
        return ws
    
    def _write(self, state):
        with open(".workspace.cvde", 'w') as F:
            json.dump(state, F, indent=4)

    def __getitem__(self, key):
        state = self._state
        return state[key]
    
    @property
    def jobs(self):
        return self['jobs']
    
    @property
    def models(self):
        return self['models']
    
    @property
    def configs(self):
        return self['configs']
    
    @property
    def tasks(self):
        return self['tasks']
    
    @property
    def datasets(self):
        return self['datasets']
        

    def delete(self, type, name):
        state = self._state
        state[type].pop(name)
        self._write(state)


    def new(self, type, name, from_template=False, job:dict=None):
        """ registers new module in workspace.
        Generate a file if from_template is true
        if registering a job, enter defaults

        """
        assert type in ['datasets', 'models', 'tasks', 'jobs',
                        'configs'], f"Unknown type: {type}.Must be one of data|model|task|config"

        if name in self.__getattribute__(type):
            logging.error(f'Not created: <{name}> ({type}) already exists')
            raise ModuleExistsError
            return
        
        if from_template:
            realize_template(type, name)

        state = self._state
        if type=='jobs':
            if job is None:
                raise NotImplementedError("default job")
            state[type].update({name:job})
        else:
            state[type].append(name)
        self._write(state)
