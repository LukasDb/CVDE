__version__ = "0.0.1"
__author__ = "Lukas Dirnberger"
__credits__ = "TUM"

__entry_points__ = {"console_scripts": ["cvde = cvde.__main__:run"]}

import cvde.tf as tf
import cvde.job as job

__all__ = ["tf", "job"]
