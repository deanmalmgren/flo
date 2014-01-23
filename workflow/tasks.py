
class Task(object):

    def out_of_sync(self):
        """test whether this task is out of sync with the stored state and
        needs to be executed
        """
        return True

    def execute(self):
        """run the specified task"""
        return None

class TaskGraph(list):
    """Simple graph implementation of a list of task nodes"""
