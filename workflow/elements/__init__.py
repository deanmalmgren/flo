from . import base
from .file_system import FileSystem

def create(graph, candidate):
    """This is a factory function that instantiates elements from a
    candidate. The candidate can either be a string or a list of
    strings.
    """

    elements = []
    if isinstance(candidate, (list, tuple)):
        for c in candidate:
            elements.extend(creates(graph, c))
    else:

        # TODO: this is where we can differentiate different
        # protocols, but for now, everything is a FileSystem thing
        # that gets passed to this method
        elements.append(FileSystem(graph, candidate))

    return elements
