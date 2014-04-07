from . import base
from .file_system import FileSystem


def get_or_create(graph, candidate_list):
    """This is a factory function that instantiates resources from a
    candidate_list. Each candidate in the candidate_list must be a
    string.
    """
    resources = []
    for candidate in candidate_list:
        if candidate is not None:

            # check if resource has already been created for this graph
            # and, if not, create it
            try:
                resource = graph.resource_dict[candidate]
            except KeyError:
                resource = FileSystem(graph, candidate)
            resources.append(resource)
    return resources
