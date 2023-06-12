from cvde.workspace_tools import (
    load_job,
    load_dataset,
    load_model,
    load_loss,
    load_metric,
    load_callback,
)
from cvde.workspace import Workspace as WS
from .job_tracker import JobTracker
import pathlib
import os
import numpy as np
from typing import TYPE_CHECKING
import streamlit as st
import cvde

import multiprocessing as mp
import threading


class JobExecutor:
    """manage running jobs"""

    @staticmethod
    def launch_job(name: str):
        """non-blocking launch job"""
        tracker = JobTracker.create(name)

        job_thread = threading.Thread(
            target=JobExecutor.run_job,
            args=(tracker.folder_name,),
            name="thread_" + tracker.unique_name,
        )
        job_thread.start()
        # launch non-blocking job

    @staticmethod
    def run_job(folder_name: str):
        tracker = JobTracker.from_log(folder_name)
        tracker.set_thread_ident()

        class Unbuffered:
            def __init__(self, stream, file):
                self.stream = stream
                self.fp = open(file, "w")

            def write(self, data):
                self.stream.write(data)
                self.stream.flush()
                self.fp.write(data)
                self.fp.flush()

            def flush(self):
                self.fp.flush()
                self.stream.flush()

        import sys

        sys.stdout = Unbuffered(sys.stdout, tracker.stdout_file)
        sys.stderr = Unbuffered(sys.stderr, tracker.stderr_file)

        job_cfg = load_job(tracker.name)

        import sys

        sys.path.append(".")  # otherwise import errors

        import silence_tensorflow.auto
        import tensorflow as tf

        available_gpus = tf.config.experimental.list_physical_devices("GPU")
        selected_gpus = [
            x for x in available_gpus if int(x.name.split(":")[-1]) in job_cfg["gpus"]
        ]
        [tf.config.experimental.set_memory_growth(gpu, True) for gpu in available_gpus]
        tf.config.set_visible_devices(selected_gpus, device_type="GPU")

        if len(selected_gpus) > 1:
            strategy = tf.distribute.MirroredStrategy()
        else:
            strategy = tf.distribute.get_strategy()

        print("ACTIVE GPUS: ", tf.config.experimental.list_physical_devices("GPU"))
        print("Running job: ", tracker.name)

        with strategy.scope():
            model: tf.keras.Model = load_model(job_cfg["Model"], **job_cfg)
            train_set = load_dataset(job_cfg["Train_Dataset"], **job_cfg)
            train_set = train_set.to_tf_dataset()

            val_set = load_dataset(job_cfg["Val_Dataset"], **job_cfg)
            if val_set is not None:
                val_set = val_set.to_tf_dataset()

        compile_kwargs = {}

        # --- LOSS ---
        loss_name = job_cfg.get("Loss", "none")
        if loss_name in WS().losses:
            loss_fn = load_loss(loss_name)
        else:
            loss_fn = getattr(tf.keras.losses, loss_name, None)

        if loss_fn is not None:
            with strategy.scope():
                loss = loss_fn(**job_cfg.get(loss_name, {}))
                compile_kwargs["loss"] = loss

        # --- OPTIMIZER ---
        opt_name = job_cfg.get("Optimizer", "none")
        if opt_name in WS().optimizers:
            raise NotImplementedError("Optimizer not implemented yet")
            opt_fn = load_optimizer(job_cfg["Optimizer"])
        else:
            opt_fn = getattr(tf.keras.optimizers, opt_name, None)

        if opt_fn is not None:
            with strategy.scope():
                optimizer = opt_fn(**job_cfg.get(opt_name, {}))
                compile_kwargs["optimizer"] = optimizer

        # METRICS
        with strategy.scope():
            metrics = []
            for metric in job_cfg.get("Metrics", []):
                if metric in WS().metrics:
                    metrics.append(load_metric(metric, **job_cfg))
                else:
                    metrics.append(metric)
        compile_kwargs["metrics"] = metrics

        # CALLBACKS
        callbacks = [cvde.tf.CVDElogger(tracker)]
        for cb_name in job_cfg.get("Callbacks", "none"):
            cb_kwargs = job_cfg.get(cb_name, {})
            if cb_name in WS().callbacks:
                cb_fn = load_callback(cb_name)
                cb_kwargs["tracker"] = tracker
            elif hasattr(cvde.tf, cb_name):
                cb_fn = getattr(cvde.tf, cb_name)
                cb_kwargs["tracker"] = tracker

            else:
                cb_fn = getattr(tf.keras.callbacks, cb_name, None)

            if cb_fn is not None:
                callbacks.append(cb_fn(**cb_kwargs))

        # print(f"Compiling Model with loss: {loss}, optimizer: {optimizer}, metrics: {metrics}")
        model.compile(**compile_kwargs)

        # print("Fitting model with callbacks: ", callbacks)
        model.fit(
            train_set,
            validation_data=val_set,
            batch_size=None,
            validation_batch_size=None,
            **job_cfg["model_fit"],
            callbacks=callbacks,
            verbose=2,
        )
