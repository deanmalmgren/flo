import os

import yaml

from . import exceptions
from . import tasks
from .utils import find_config_path

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
