from . import base
from .file_system import FileSystem

def get_or_create(graph, candidate):
    """This is a factory function that instantiates resources from a
    candidate. The candidate can either be a string or a list of
    strings.
    """

    resources = []
    if isinstance(candidate, (list, tuple)):
        for c in candidate:
            resources.extend(creates(graph, c))
    elif candidate is not None:

        # check if resource has already been created for this graph
        # and, if not, create it
        try:
            resource = graph.resource_dict[candidate]
        except KeyError:
            # TODO: this is where we can differentiate different
            # protocols, but for now, everything is a FileSystem thing
            # that gets passed to this method
            resource = FileSystem(graph, candidate)

        resources.append(resource)

    return resources

