# TODO UPDATE FOR CHANGES

# Computer Vision Development Environment (CVDE)
This project aims to provide a framework for Computer Vision experiments. The framework suggests a standard directory structure for the project and provides a set of tools to facilitate the development process. The framework is based on the following principles:
* **Modularity**: The framework is composed of a set of modules, each module is responsible for a specific task. The modules are designed to be independent and can be used separately.
* **Extensibility**: The framework is designed to be easily extended. The user can add new modules or modify existing ones.
* **Simplicity**: The framework is designed to be simple and easy to use. The user can start using the framework with minimal effort.

## Getting Started
- clone this repository in run `pip install .` in the root directory
- run `cvde init` to create the project structure in an empty folder
- run `cvde gui [path/to/workspace]` to access the GUI from your browser
- `cvde --help` for more information
- `cvde init` will also attempt to create a `.vscode/launch.json` to be used with Visual Studio Code for debugging.

## Notes
- for now, only Tensorflow is supported, but should be easily extended to be backend agnostic

## Ideas and Concepts
- As an example of a project using CVDE check out [PVN3D](https://github.com/LukasDb/PVN3D)
- In one project your data loaders should follow the same interfaces, so they can be easily swapped.
- The same goes for models, etc...
- Parametrize everything and add the parameters to config `.yaml` files. You can then easily make changes from the GUI and run different experiments.
- Never define default values for parameters in your code.

**Datasets**
- Datasets should inherit from `cvde.tf.Dataset`. Implement `__init__`, `__getitem__`, `__len__` and `visualize_example` methods.
- `__getitem__` should return a dict that contains tensors or np.arrays, then you can use `.from_cache()` and `.cache()` to load your dataset into a sharded tfrecord dataset for better performance. Not necessary if you use high-performance dataloaders from 6IMPOSE_Data.
- In `visualize_example` use functions from [streamlit](https://streamlit.io) to visualize one example of your dataset, as returned by `__getitem__`. This will be used in the Data explorer of the GUI
- Since `__getitem__` most likely outputs a non-batched example (for visualization), perform batching in your training job.

**Jobs**
- To create a job, create a new file in `jobs/`, inherit from `cvde.job.Job` and implement `__init__`, `run` and `on_terminate` methods.
- You can access the parameters of your Config file using `self.config: Dict[str, Any]`
- To log data during your job, use `self.logger.log(name: str, value, index: int)`. The data can then be inspected in the GUI->Inspector.
- Currently scalars, and images are supported. CVDE will try to automatically detect the type of the data you are logging, using the shape. For images, use the shape `[H, W, C]` or `[H, W]` for grayscale images.
- The index in `self.logger.log` is used to assign an order to the logged data. E.g. if you log the loss after each training epoch, then you should assign the epoch number as index. This will be used to plot the loss over time in the GUI->Inspector.
- If you want to save weights (or maybe other data) it is highly recommended to use the paths of `self.logger.weights_root` or generic `self.logger.root` referreing to the folder in log/ where the data will be saved. This way the data will be automatically saved in the correct folder.
- Your job should then be available in the Job Launcher of the GUI. Choose your job and your configuration. Set environment variables (like GPUs) and specify if this job should wait for other scheduled jobs. You can then schedule multiple jobs to run in parallel or sequentially according to your constraints. Note: When your job is scheduled, the current state of your code and your configuration will be used for launching the job. This is based on git commits and diffs, therefore gitignored files are not taken into account!

**Configs**
- For now yaml files are used to keep the configuration. You can use the GUI to edit the config files.

**Git Tracking**
- Inspired by [Dr. Watson](https://juliadynamics.github.io/DrWatson.jl/dev/) for Julia, CVDE uses Git to store the state of your code when you run an experiment. This way you can always go back to the exact code that was used to run an experiment.
- Git tracking will be enabled when you initialize a CVDE Workspace
- To enable Git Tracking on a previously un-initialized CVDE Workspace run `cvde init` again in the the root directory of your workspace and follow the instructions.
- If Git Tracking is enabled, every time you submit a job the current state of your code will be captured by saving the current commit hash and the diff of the current state with the last commit. This will be saved in the log folder of the job. in the log_folder/workspace, a cloned copy of your repository will be used to execute your job. This way you can always go back to the exact code that was used to run an experiment.