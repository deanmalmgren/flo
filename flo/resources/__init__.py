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
