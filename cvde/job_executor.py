from cvde.workspace_tools import load_config, load_dataset, load_model, load_task_fn
from cvde.job_tracker import JobTracker
import importlib
import traceback


def execute_job(name: str, task: str, config_name: str, model_name: str, train_ds: str, val_ds: str):
    tracker = JobTracker.create(
        name, task, config_name, model_name, train_ds, val_ds)
    
    config = load_config(config_name)

    for key in ['task', 'model', 'shared', 'train_config', 'val_config']:
        if config[key] is None:
            config[key] = {}

    task_fn = load_task_fn(task)
    try:
        model = load_model(model_name, **config["model"], **config["shared"])
    except ModuleNotFoundError:
        print(traceback.format_exc())
        model = None
    try:
        print(config)
        train_set = load_dataset(
            train_ds, **config['train_config'], **config["shared"])
    except ModuleNotFoundError:
        print(traceback.format_exc())
        train_set = None
    try:
        val_set = load_dataset(
            val_ds, **config['val_config'], **config["shared"])
    except ModuleNotFoundError:
        print(traceback.format_exc())
        val_set = None

    with tracker:
        task_fn(tracker, model=model, train_set=train_set,
                val_set=val_set, **config['task'], **config["shared"])
