from . import exceptions

class Task(object):

    def __init__(self, creates=None, depends=None, alias=None, command=None, 
                 **kwargs):
        self.creates = creates
        self.depends = depends
        self.command = command
        self.alias = alias
        self.other = kwargs

        # quick type checking to make sure the tasks in the
        # configuration file are valid
        if self.creates is None:
            raise exceptions.InvalidTaskDefinition(
                "every task must define a `creates`"
            )
        if self.command is None:
            raise exceptions.InvalidTaskDefinition(
                "every task must define a `command`"
            )

    def out_of_sync(self):
        """test whether this task is out of sync with the stored state and
        needs to be executed
        """
        return True

    def execute(self):
        """run the specified task"""
        return None

class TaskGraph(object):
    """Simple graph implementation of a list of task nodes"""

    def __init__(self):
        self.tasks = []

    def add(self, task):
        self.tasks.append(task)

    def __iter__(self):
        return iter(self.tasks)
