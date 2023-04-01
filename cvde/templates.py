import yaml
import os


templates = {
    'tasks': f"def main(*, model, train_set, val_set, **kwargs):\n    pass",
    'datasets': f"def get_dataloader(**kwargs):\n    return []",
    'models': f"def get_model(**kwargs):\n    return model",
    'configs': yaml.dump(
        {'model': "model_name",
         'train_set': 'train_set', 'val_set': 'val_set',
         'task_config': {}, 'model_config': {},
         'train_data_config': {}, 'val_data_config': {}},
        indent=2)
}


def realize_template(type, name):
    suffix = '.yml' if type == 'configs' else '.py'

    with open(os.path.join(type, name + suffix), "w") as F:
        F.write(templates[type])
