from cvde.workspace_tools import load_config, load_dataset, load_model, load_task_fn
from cvde.job_tracker import JobTracker
import importlib


def execute_job(name:str, task: str, config: str, model_name: str, train_ds: str, val_ds: str):
    tracker = JobTracker.create(name, task, config, model_name, train_ds, val_ds)

    config = load_config(config)
    task_fn = load_task_fn(task)
    try:
        model = load_model(model_name, config["model"])
    except ModuleNotFoundError:
        model = None
    try:
        train_set = load_dataset(train_ds, config['train_config'])
    except ModuleNotFoundError:
        train_set = None
    try:
        val_set = load_dataset(val_ds, config['val_config'])
    except ModuleNotFoundError:
        val_set = None
    

    task_fn(tracker, model=model, train_set=train_set,
                     val_set=val_set, **config['task'])