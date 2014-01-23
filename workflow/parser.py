import os

from . import exceptions
from . import tasks

def find_config_path(config_filename="workflow.yaml"):
    """Recursively decend into parent directories looking for the 
    """
    directory = os.getcwd()
    config_path = ''
    while directory:
        filename = os.path.join(directory, config_filename)
        if os.path.exists(filename):
            config_path = filename
            break
        directory = os.path.sep.join(directory.split(os.path.sep)[:-1])
    if not config_path:
        raise exceptions.ConfigurationNotFound(
            config_filename,
            os.getcwd()
        )
    return config_path

def load_task_graph(config_path):
    return tasks.TaskGraph()
