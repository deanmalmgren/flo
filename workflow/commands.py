import time
from distutils.util import strtobool

from .parser import load_task_graph
from . import colors

def clean(force=False):
    """Remove all `creates` targets defined in workflow
    """

    # load the task graph
    task_graph = load_task_graph()

    # print a warning message before removing all tasks
    if not force:
        print(colors.red(
            "Please confirm that you want to delete the following files."
        ))
        time.sleep(0.5)
        for task in task_graph:
            print(task.creates_message())
        yesno = raw_input(colors.red("Delete aforementioned files? [Y/n] "))
        if yesno == '':
            yesno = 'y'
        if not strtobool(yesno):
            return

    # for every task in the task graph, remove the corresponding
    # `creates` targets
    for task in task_graph:
        task.clean()

def execute():
    """Execute the task workflow.
    """

    # load the task graph
    task_graph = load_task_graph()

    # iterate through every task in the task graph and execute every
    # task that is out of sync with our last stored state
    did_task = False
    for task in task_graph:
        if not task.in_sync():
            task.execute()
            did_task = True

    # if no tasks were executed, then alert the user that nothing
    # needed to be run
    if not did_task:
        print("No tasks were run in the workflow defined in '%s'" % (
            task_graph.config_path,
        ))
        
    # otherwise, we need to recalculate hashes for everything that is
    # out of sync
    task_graph.save_state()
