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
from typing import TYPE_CHECKING
import docker
import docker.models.containers
import streamlit as st
import cvde


class JobExecutor:
    """manage running jobs"""

    @staticmethod
    def launch_job(name: str):
        """non-blocking launch job"""
        tracker = JobTracker.create(name)

        client = docker.from_env()
        # build image for CVDE if not exists
        cvde_tag = "cvde/cvde"
        imgs = [image.tags[0].split(":")[0] for image in client.images.list()]
        if cvde_tag not in imgs:
            with st.spinner("Building CVDE base image"):
                client.images.build(
                    path=str(pathlib.Path(__file__).parent.parent),
                    tag=cvde_tag,
                    rm=True,
                )

        ws_tag = f"{WS().name.lower()}/{WS().name.lower()}"

        # build image for current project if not exists
        imgs = [image.tags[0].split(":")[0] for image in client.images.list()]
        if ws_tag not in imgs:
            with st.spinner("Building docker image"):
                client.images.build(path=".", tag=ws_tag, rm=True)

        container = client.containers.run(
            ws_tag,
            f"execute {tracker.folder_name}",
            detach=True,
            device_requests=[
                docker.types.DeviceRequest(device_ids=["0"], capabilities=[["gpu"]])
            ],
            volumes={
                os.getcwd(): {"bind": "/ws", "mode": "rw"},
                "/home/lukas/dev/datasets/blender/blender/": {
                    "bind": "/home/lukas/dev/datasets/blender/blender/",  # TODO fix mounting datasets
                    "mode": "rw",
                },
                "/home/lukas/dev/CVDE": {
                    "bind": "/cvde",
                    "mode": "rw",
                },  # mount CVDE package for pip install (debugging)
            },
            # user=os.getuid(),
            working_dir="/ws",
            name=tracker.folder_name,
        )

    @staticmethod
    def run_job(folder_name: str):
        tracker = JobTracker.from_log(folder_name)
        job_cfg = load_job(tracker.name)

        import sys

        sys.path.append(".")  # otherwise import errors

        import os

        os.environ["CUDA_VISIBLE_DEVICES"] = ",".join([str(x) for x in job_cfg["gpus"]])

        with tracker:
            import tensorflow as tf

            gpus = tf.config.experimental.list_physical_devices("GPU")
            [tf.config.experimental.set_memory_growth(gpu, True) for gpu in gpus]

            print("ACTIVE GPUS: ", tf.config.experimental.list_physical_devices("GPU"))

            print("Running job: ", tracker.name)
            model: tf.keras.Model = load_model(job_cfg["Model"], **job_cfg)
            train_set = load_dataset(job_cfg["Train_Dataset"], **job_cfg)
            val_set = load_dataset(job_cfg["Val_Dataset"], **job_cfg)
            train_set = train_set.to_tf_dataset()
            val_set = val_set.to_tf_dataset()

            # find either custom loss or use as string and hope its a tensorflow loss
            if job_cfg["Loss"] in WS().losses:
                loss = load_loss(job_cfg["Loss"], **job_cfg)
            else:
                loss = job_cfg["Loss"]
            
            opt_name = job_cfg["Optimizer"]
            if opt_name in WS().optimizers:
                raise NotImplementedError("Optimizer not implemented yet")
                optimizer = load_optimizer(job_cfg["Optimizer"], **job_cfg)
            else:
                optimizer = getattr(tf.keras.optimizers, opt_name)(**job_cfg[opt_name])

            metrics = []
            for metric in job_cfg["Metrics"]:
                if metric in WS().metrics:
                    metrics.append(load_metric(metric, **job_cfg))
                else:
                    metrics.append(metric)

            callbacks = [cvde.tf.CVDElogger(tracker)]
            for callback in job_cfg["Callbacks"]:
                if callback in WS().callbacks:
                    callbacks.append(load_callback(callback, tracker, **job_cfg))
                else:
                    callbacks.append(getattr(tf.keras.callbacks, callback)(**job_cfg))

            print(
                f"Compiling Model with loss: {loss}, optimizer: {optimizer}, metrics: {metrics}"
            )
            model.compile(loss=loss, optimizer=optimizer, metrics=metrics)

            print("Fitting model with callbacks: ", callbacks)
            model.fit(
                train_set,
                validation_data=val_set,
                batch_size=None,
                validation_batch_size=None,
                **job_cfg["model_fit"],
                callbacks=callbacks,
                verbose=2,
            )