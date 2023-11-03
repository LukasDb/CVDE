__version__ = "0.0.1"
__author__ = "Lukas Dirnberger"
__credits__ = "TUM"

__entry_points__ = {"console_scripts": ["cvde = cvde.__main__:run"]}

import cvde.tf as tf
import cvde.workspace_tools as ws_tools


import cvde.gui as gui

from cvde.workspace import Workspace as WS
import cvde.job as job
from cvde.threaded_printer import ThreadPrinter

__all__ = ["gui", "tf", "job", "ws_tools", "WS", "ThreadPrinter"]
