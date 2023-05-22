from typing import Dict
import tensorflow as tf
import os
import yaml
import importlib
import pathlib
import cvde



def load_module(base_module, module_name):
    files = list(
        x
        for x in pathlib.Path(base_module).iterdir()
        if x.is_file() and not x.stem.startswith("_")
    )

    for file in files:
        import_path = base_module + "." + file.stem
        module = importlib.import_module(import_path)
        if hasattr(module, module_name):
            break
    importlib.reload(module)
    return module


def load_metric(__metric_name, **kwargs) -> tf.keras.metrics.Metric:
    metric_module = load_module("metrics", __metric_name)
    metric = getattr(metric_module, __metric_name)
    metric = metric(**kwargs.get(__metric_name, {}))
    return metric


def load_callback(__callback_name, tracker, **kwargs) -> tf.keras.callbacks.Callback:
    callback_module = load_module("callbacks", __callback_name)
    callback = getattr(callback_module, __callback_name)
    callback = callback(tracker, **kwargs.get(__callback_name, {}))
    return callback


def load_dataset(__dataset_name, **kwargs) -> cvde.tf.Dataset:
    dataset_module = load_module("datasets", __dataset_name)
    ds = getattr(dataset_module, __dataset_name)
    return ds(**kwargs.get(__dataset_name, {}))


def load_model(__model_name, **kwargs) -> tf.keras.Model:
    model_module = load_module("models", __model_name)
    model = getattr(model_module, __model_name)
    model = model(**kwargs.get(__model_name, {}))
    return model


def load_loss(__loss_name, **kwargs) -> tf.keras.losses.Loss:
    loss_module = load_module("losses", __loss_name)
    loss = getattr(loss_module, __loss_name)
    loss = loss(**kwargs.get(__loss_name, {}))
    return loss


def load_job(job_name) -> Dict:
    with open(os.path.join("jobs", job_name + ".yml")) as F:
        job: Dict = yaml.safe_load(F)
    return job
