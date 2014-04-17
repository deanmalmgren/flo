import os
import re

from . import base
from .file_system import FileSystem
from ..exceptions import NonUniqueTask


def get_or_create(task, candidate_list, creates_or_depends):
    """This is a factory function that instantiates resources from a
    candidate_list.
    """
    resources = []
    for candidate in candidate_list:
        if candidate is not None:

            # instantiate a new resource if it doesn't already exist
            try:
                resource = task.graph.resource_dict[candidate]
            except KeyError:
                resource = FileSystem(task.graph, candidate)

            # bind the task to the appropriate data structure
            # depending on whether this task creates this resource or
            # depends on this resource.
            if creates_or_depends == 'creates':
                resource.add_creates_task(task)
            else:
                resource.add_depends_task(task)

            resources.append(resource)
    return resources


def add_to_task(task):
    """This factory function adds the appropriate `creates` or `depends`
    resources for the specified task.
    """
    # instantiate the resources associated with this task here
    # to make sure we can resolve aliases if they exist.
    get_or_create(task, task.depends_list, 'depends')
    if not task.is_pseudotask():
        get_or_create(task, task.creates_list, 'creates')


def find_regexp_matches(root_directory, regexp_str):
    """This function returns a list of all filenames matching regexp_str
    in the form of a regular expression match.
    """
    regexp_matches = []
    regexp = re.compile(regexp_str)
    # NOTE: this os.walk is probably the stupidest possible way to do
    # this. I'm sure there's a more efficient way to address this
    # issue, but I'm not going to worry about that yet.
    #
    # NOTE: This only works for files right now. no support for
    # directories (for better or worse) and its not terribly obvious
    # whether/how this extends to other resource protocols (e.g.,
    # mysql:database/table)
    filesystem_crawler = os.walk(root_directory, followlinks=True)
    for directory, dirnames, filenames in filesystem_crawler:
        for filename in filenames:
            abs_filename = os.path.join(directory, filename)
            rel_filename = os.path.relpath(abs_filename, root_directory)
            match = regexp.match(rel_filename)
            if match:
                regexp_matches.append(match)
    return regexp_matches

