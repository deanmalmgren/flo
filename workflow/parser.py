"""This set of modules is intended to parse and process the
CONFIG_FILENAME, workflow.yaml
"""

import os

import yaml

from . import exceptions
from . import tasks

# TODO: probably this should be configurable (and even specified on
# the command line somehow)
CONFIG_FILENAME = "workflow.yaml"

def find_config_path():
    """Recursively decend into parent directories looking for the 
    """

    config_path = ''
    directory = os.getcwd()
    while directory:
        filename = os.path.join(directory, CONFIG_FILENAME)
        if os.path.exists(filename):
            config_path = filename
            break
        directory = os.path.sep.join(directory.split(os.path.sep)[:-1])
    if not config_path:
        raise exceptions.ConfigurationNotFound(
            CONFIG_FILENAME,
            os.getcwd()
        )
    return config_path

def load_task_graph():
    """Load the task graph from the configuration file located at
    config_path
    """

    # look for workflow configuration file if it isn't already
    # specified
    config_path = find_config_path()

    # load the data
    with open(config_path) as stream:
        config_yaml = yaml.load_all(stream.read())

    # convert each yaml to a task and add it to the graph
    task_graph = tasks.TaskGraph(config_path)
    for task_data in config_yaml:
        task = tasks.Task(**task_data)
        task_graph.add(task)
    task_graph.link_dependencies()

    # load the state of each task's `creates` and `depends` elements
    task_graph.load_state()

    return task_graph

def get_available_tasks():
    """Return the available set of tasks that are specified in the
    configuration file. These are returned in the order they are
    specified in the configuration files.
    """
    task_graph = load_task_graph()
    return [task.id for task in task_graph.task_list]

def get_available_archives():
    """Return the list of available archives that are stored in
    .workflow/archives
    """
    task_graph = load_task_graph()
    return task_graph.get_available_archives()
