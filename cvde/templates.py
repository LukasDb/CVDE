import os

model_template = """
def get_model(weights_path=None, **kwargs):
    pass
"""


dataset_template = """
import cvde.data_types as dt


def get_dataloader(**kwargs):
    pass

def get_dataspec(**kwargs):
    pass
"""

config_template = """
# shared kwargs for model, datasets and task
shared:

# kwargs for get_model
model:

# kwargs for main of a task
task:

# kwargs for get_dataloader
train_config:

# kwargs for get_dataloader
val_config:

"""

task_template = """
from cvde.job_tracker import JobTracker

def main(tracker: JobTracker, *, model, train_set, val_set, **kwargs):
    pass

"""

templates = {
    'tasks': task_template,
    'datasets': f"def get_dataloader(**kwargs):\n    return []",
    'models': model_template,
    'configs': config_template,
}


def realize_template(type, name):
    suffix = '.yml' if type == 'configs' else '.py'

    with open(os.path.join(type, name + suffix), "w") as F:
        F.write(templates[type])
