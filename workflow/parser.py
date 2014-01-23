import os

import yaml

from . import exceptions
from . import tasks

def find_config_path(config_filename="workflow.yaml"):
    """Recursively decend into parent directories looking for the 
    """

    config_path = ''
    directory = os.getcwd()
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
    """Load the task graph from the configuration file located at
    config_path
    """

    # load the data
    with open(config_path) as stream:
        config_yaml = yaml.load_all(stream.read())

    # convert each yaml to a task and add it to the graph
    task_graph = tasks.TaskGraph()
    for task_data in config_yaml:
        task = tasks.Task(**task_data)
        task_graph.add(task)

    return task_graph
