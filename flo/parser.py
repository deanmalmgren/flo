"""This set of modules is intended to parse and process the
CONFIG_FILENAME, flo.yaml, into a TaskGraph object. This also
provides a singleton instance of the TaskGraph (often called
'task_graph') that can be accessed from anywhere.

"""

import os
import copy

import yaml

from . import exceptions
from . import tasks

# TODO: probably this should be configurable (and even specified on
# the command line somehow)
CONFIG_FILENAME = "flo.yaml"
TASKS_KEY = 'tasks'

# these variables are used as a global cache to only parse the yaml
# into python objects and create a TaskGraph instance *once* in the
# entire workflow
_task_kwargs_list = None
_task_graph = None


def find_config_path():
    """Recursively decend into parent directories looking for the config
    file. Raise an error if none found.
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


def config_yaml2task_kwargs_list(config_yaml):
    """convert the config_yaml iterator into python dictionaries as
    necessary. this makes it possible to have global variables and
    tasks embedded in the YAML under a something with the key
    TASKS_KEY
    """
    task_kwargs_list = []
    uses_global_config = False
    for i, yaml_obj in enumerate(config_yaml):
        if i == 0 and TASKS_KEY in yaml_obj:
            uses_global_config = True

            global_config = copy.deepcopy(yaml_obj)
            del global_config[TASKS_KEY]

            for task_data in yaml_obj[TASKS_KEY]:
                task_data.update(global_config)
                task_kwargs_list.append(task_data)
        elif not uses_global_config:
            task_kwargs_list.append(yaml_obj)
    return task_kwargs_list


def get_task_kwargs_list():
    """Get a list of dictionaries that are read from the flo.yaml
    file and collapse the global variables into each task.
    """
    global _task_kwargs_list
    if _task_kwargs_list is None:
        # get workflow configuration file
        config_path = find_config_path()

        # load the data
        with open(config_path) as stream:
            config_yaml = yaml.load_all(stream.read())
        _task_kwargs_list = config_yaml2task_kwargs_list(config_yaml)
    return _task_kwargs_list


def load_task_graph():
    """Load the task graph from the configuration file located at
    config_path
    """
    global _task_graph
    if _task_graph is not None:
        return _task_graph

    # convert each task_kwargs into a Task object and add it to the
    # TaskGraph
    _task_graph = tasks.TaskGraph(find_config_path(), get_task_kwargs_list())
    return _task_graph
