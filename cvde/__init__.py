__version__ = "0.0.1"
__author__ = "Lukas Dirnberger"
__credits__ = "TUM"

__entry_points__ = {"console_scripts": ["cvde = cvde.__main__:run"]}

# setup mp
import multiprocessing as mp
import os

try:
    mp.set_start_method("spawn")
except RuntimeError:
    pass

# setup tensorflow
if mp.current_process().name == "MainProcess":
    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"


import silence_tensorflow.auto
import tensorflow

# --- constants definition ---
import typing
from typing import Any


# class types:
#     LOSS_TYPE = tf.keras.losses.Loss | typing.Callable[[Any], Any]


# --- modules ---
import cvde.tf as tf
import cvde.gui as gui
import cvde.job as job
from cvde.workspace import Workspace
from cvde.threaded_printer import ThreadPrinter

# --- colored printing for different processes ---
import sys

sys.stdout = ThreadPrinter(sys.stdout)
sys.stderr = ThreadPrinter(sys.stderr)

__all__ = [
    "types",
    "Dataset",
    "gui",
    "job",
    "ThreadPrinter",
]
