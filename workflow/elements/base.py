"""Base element here
"""

import hashlib

class BaseElement(object):
    """An element is any `creates` or `depends` or `task` that is
    mentioned in a workflow.yaml. An element can be on the file
    system, in a database, etc.

    The basic functionality of an element is to (i) keep track of
    which tasks it is associated with and (ii) assess the state of the
    element and whether it is in sync
    """

    def __init__(self, graph, name):
        self.graph = graph
        self.name = name

    def add_depends(self, task):
        raise NotImplementedError

    def add_creates(self, task):
        raise NotImplementedError

    @property
    def root_directory(self):
        """Easy access to the graph's root_directory, which is stored once for
        every task"""
        return self.graph.root_directory

    def _get_stream_state(self, stream, block_size=2**20):
        """Read in a stream in relatively small `block_size`s to make sure we
        won't have memory problems on BIG DATA streams.
        http://stackoverflow.com/a/1131255/564709
        """
        state = hashlib.sha1()
        while True:
            data = stream.read(block_size)
            if not data:
                break
            state.update(data)
        return state.hexdigest()

    def get_state(self):
        """Get the current state of this element. If the element does
        not exist, throw an error.
        
        This method must be overwritten by any child classes.
        """
        raise NotImplementedError("Must implement get_state for child classes")
        
    def state_in_sync(self, element):
        """Check the stored state of this element compared with the current
        state of this element. If they are the same, then this element
        is in_sync.
        """

        # XXXX THIS IS A MESS

        # if the element is None type (for example, when you only
        # specify a `creates` and a `command`, but no `depends`),
        # consider this in sync at this stage. 
        if element is None:
            return True

        # Get the stored state value if it exists. If it doesn't exist,
        # then automatically consider this element out of sync
        stored_state = self.graph.before_element_states.get(element, None)

        # get the current state of the file just before runtime
        current_state = self.get_state()

        print 'STATE', stored_state, current_state

        # store the after element state here. If its none, its updated
        # at the very end
        self.graph.after_element_states[element] = current_state

        # element is in_sync if the stored and current states are the same
        return stored_state == current_state

