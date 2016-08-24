"""This set of modules is intended to parse and process the
CONFIG_FILENAME, flo.yaml, into a TaskGraph object. This also
provides a singleton instance of the TaskGraph (often called
'task_graph') that can be accessed from anywhere.

"""

import os
import copy

import yaml

from . import exceptions
from .tasks import TaskGraph
from .decorators import memoize

# these are the default values that are expected if nothing else is
# specified on the command line
CONFIG_FILENAME = "flo.yaml"
TASKS_KEY = 'tasks'


def find_config_path(config=None):
    """Recursively decend into parent directories looking for the config
    file. Raise an error if none found.
    """

    # if the config is specified on the command line, test to see if
    # the config file exists
    if config is not None:
        config_path = os.path.abspath(os.path.join(os.getcwd(), config))
        if not os.path.exists(config_path):
            raise exceptions.ConfigurationNotFound(
                config,
                os.getcwd()
            )
        return config_path

    # otherwise, recursively check parent directories of the current
    # directory for anything named CONFIG_FILENAME
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


@memoize
def get_task_kwargs_list(config=None):
    """Get a list of dictionaries that are read from the flo.yaml
    file and collapse the global variables into each task.
    """

    # get workflow configuration file
    config_path = find_config_path(config=config)

    # load the data
    with open(config_path) as stream:
        config_yaml = yaml.load_all(stream.read())
    try:
        return config_yaml2task_kwargs_list(config_yaml)
    except yaml.constructor.ConstructorError as error:
        raise exceptions.YamlError(config_path, error)


@memoize
def load_task_graph(config=None):
    """Load the task graph from the configuration file located at
    config_path
    """

    config_path = find_config_path(config=config)

    # convert each task_kwargs into a Task object and add it to the
    # TaskGraph
    return TaskGraph(config_path, get_task_kwargs_list(config_path))
