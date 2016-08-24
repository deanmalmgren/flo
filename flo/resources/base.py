"""Base resource here
"""

import hashlib


class BaseResource(object):
    """A resource is any `creates` or `depends` or `task` that is
    mentioned in a flo.yaml. A resource can be on the file
    system, in a database, etc.

    The basic functionality of an resource is to assess the state of the
    resource and whether it is in sync.
    """

    def __init__(self, graph, name):
        self.graph = graph
        self.name = name

        # add this resource to the graph's resource_dict, which globally
        # stores all of the resources associated with this workflow
        if name in self.graph.resource_dict:
            raise ValueError(
                "Resource '%s' already exists in this graph" % name
            )
        self.graph.resource_dict[name] = self

        # these are data structures that are used to track tasks that
        # have dependencies through this resource
        self.creates_task = None
        self.depends_tasks = []

    def __repr__(self):
        return self.name + ':' + str(id(self))

    def add_creates_task(self, task):
        if self.creates_task is not None:
            msg = "Resource '%s' is created by more than one task" % self.name
            raise NonUniqueTask(msg)
        self.creates_task = task
        task.creates_resources.append(self)

    def add_depends_task(self, task):
        self.depends_tasks.append(task)
        task.depends_resources.append(self)

    def delete(self):
        self.graph.resource_dict.pop(self.name)
        if self.creates_task:
            self.creates_task.creates_resources.remove(self)
        for task in self.depends_tasks:
            task.depends_resources.remove(self)
        del self

    @property
    def root_directory(self):
        """Easy access to the graph's root_directory, which is stored once for
        every task"""
        return self.graph.root_directory

    def get_stream_state(self, stream, block_size=2**20):
        """Read in a stream in relatively small `block_size`s to make sure we
        won't have memory problems on BIG DATA streams.
        http://stackoverflow.com/a/1131255/564709
        """
        # TODO: this is called relatively frquently and is almost
        # certainly IO bound. think about optimizing for speed if
        # necessary by possibly reading random chunks of a stream
        # instead of the whole darn thing
        state = hashlib.sha1()
        while True:
            data = stream.read(block_size)
            if not data:
                break
            try:
                state.update(data)
            except TypeError:
                # Assuming this is caused by getting Unicode
                # Unicode must be encoded before hashing
                state.update(data.encode('utf8'))
        return state.hexdigest()

    def get_previous_state(self):
        """Get the previous state of this resource prior to this run. If the
        resource does not exist, throw an error.
        """
        return self.graph.get_state_from_storage(self.name)

    def get_current_state(self):
        """Get the current state of this resource. If the resource does
        not exist, throw an error.

        This method must be overwritten by any child classes.

        TODO: need to figure out a way to avoid running this method
        multiple times on the same resource during a single flo
        run. this is more of a performance issue that can be revisited
        later as it becomes an issue. can maybe cache somehow?
        """
        raise NotImplementedError(
            "Must implement current_state for child classes"
        )

    def state_in_sync(self):
        """Check the stored state of this resource compared with the current
        state of this resource. If they are the same, then this resource
        is in_sync.
        """
        return self.get_previous_state() == self.get_current_state()

    def get_filename(self):
        """This gets a filename for a (possibly temporary) storage location
        for a resource on disk. In situations where the resource is
        already on disk, this is very simple. In situations where the
        resource is not natively on disk (e.g., a database or a remote
        database), this method should create the corresponding
        resource on the local disk.
        """
        raise NotImplementedError(
            "Must implement get_filename for child classes"
        )

    def exists(self):
        """Check to see if the resource exists."""
        raise NotImplementedError
