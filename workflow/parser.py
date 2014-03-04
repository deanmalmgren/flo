"""This set of modules is intended to parse and process the
CONFIG_FILENAME, workflow.yaml
"""

import os
import copy

import yaml

from . import exceptions
from . import tasks

# TODO: probably this should be configurable (and even specified on
# the command line somehow)
CONFIG_FILENAME = "workflow.yaml"
TASKS_KEY = 'tasks'

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

    # convert the config_yaml iterator into python dictionaries as
    # necessary. this makes it possible to have global variables and
    # tasks embedded in the YAML under a something with the key
    # TASKS_KEY
    task_list = []
    uses_global_config = False
    for i, yaml_obj in enumerate(config_yaml):
        if i==0 and yaml_obj.has_key(TASKS_KEY):
            uses_global_config = True

            global_config = copy.deepcopy(yaml_obj)
            del global_config[TASKS_KEY]

            for task_data in yaml_obj[TASKS_KEY]:
                task_data.update(global_config)
                task_list.append(task_data)
        elif not uses_global_config:
            task_list.append(yaml_obj)

    # convert each yaml to a task and add it to the graph
    task_graph = tasks.TaskGraph(config_path)
    for task_data in task_list:
        task = tasks.Task(task_graph, **task_data)
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
