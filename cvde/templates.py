import json
import os

{
    "model": "mnist_densenet",
    "train_set": "mnist_train",
    "val_set": "mnist_val",
    "task_config": {
        "num_epochs": 6
    },
    "model_config": {
        "dim_hidden": 128,
        "learn_rate": 0.001
    },
    "train_data_config": {},
    "val_data_config": {}
}

templates = {
    'datasets': f"def get_dataloader(**kwargs):\n    return []",
    'models': f"def get_model(**kwargs):\n    return model",
    'configs': json.dumps(
        {'model': "model_name",
         'train_set': 'train_set', 'val_set': 'val_set',
         'task_config': {}, 'model_config': {},
         'train_data_config': {}, 'val_data_config': {}},
        indent=4)
}


def generate_template(type, name):
    suffix = '.json' if type == 'config' else '.py'

    with open(os.path.join(type, name + suffix), "w") as F:
        F.write(templates[type])


def write_vs_launch_file():
    try:
        os.makedirs('.vscode')
    except FileExistsError:
        pass

    launch_file = os.path.join('.vscode', 'launch.json')
    if os.path.isfile(launch_file):
        with open(launch_file) as F:
            launch = json.load(F)
    else:
        launch = {"version": "0.2.0", "configurations": []}

    launch["configurations"].append({
        "name": "Launch GUI",
                "type": "python",
                "request": "launch",
                "module": "cvde",
                "args": [
                    "gui"
                ],
        "justMyCode": True
    })

    with open(launch_file, 'w') as F:
        json.dump(launch, F, indent='\t')
