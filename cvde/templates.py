import yaml
import os

model_template="""
from cvde.job_tracker import JobTracker

def get_model(tracker: JobTracker, *, weights_path=None, **kwargs):
    # TODO
    return model
"""


dataset_template="""
import cvde.data_types as dt


def get_dataloader(**kwargs):
    pass

def get_dataspec(**kwargs):
    pass
"""



templates = {
    'tasks': f"def main(*, model, train_set, val_set, **kwargs):\n    pass",
    'datasets': f"def get_dataloader(**kwargs):\n    return []",
    'models': model_template,
    'configs': "# shared kwargs for model, datasets and task\nshared: null\n\n# kwargs for get_model\nmodel:\n\n# kwargs for main of a task\ntask:\n\n# kwargs for get_dataloader\ntrain_config:\n\n# kwargs for get_dataloader\nval_config:\n\n",
}


def realize_template(type, name):
    suffix = '.yml' if type == 'configs' else '.py'

    with open(os.path.join(type, name + suffix), "w") as F:
        F.write(templates[type])
