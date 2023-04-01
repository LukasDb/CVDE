import yaml
import os


templates = {
    'tasks': f"def main(*, model, train_set, val_set, **kwargs):\n    pass",
    'datasets': f"def get_dataloader(**kwargs):\n    return []",
    'models': f"def get_model(**kwargs):\n    return model",
    'configs': "# kwargs for get_model\nmodel:\n\n# kwargs for main of a task\ntask:\n\n# kwargs for get_dataloader\ntrain_config:\n\n# kwargs for get_dataloader\nval_config:\n\n",
}


def realize_template(type, name):
    suffix = '.yml' if type == 'configs' else '.py'

    with open(os.path.join(type, name + suffix), "w") as F:
        F.write(templates[type])
