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

def execute(force=False):
    """Execute the task workflow.
    """

    # load the task graph
    task_graph = load_task_graph()

    # iterate through every task in the task graph and find the set of
    # tasks that have to be executed. we do this first so we can alert
    # the user as to how long this workflow will take
    out_of_sync_tasks = []
    for task in task_graph:

        # regardless of whether we force the execution of the command,
        # run the in_sync method, which calculates the state of the
        # task and all `creates` / `depends` elements
        if not task.in_sync() or force:
            out_of_sync_tasks.append(task)

    # report the minimum amount of time this will take to execute and
    # execute all tasks
    if out_of_sync_tasks:
        print(task_graph.duration_message(out_of_sync_tasks))
        for task in task_graph:
            # TODO: try to find better way to do this when we
            # implement the dependency chains. this reruns the in_sync
            # method which can be relatively slow for BIG data
            if not task.in_sync() or force:
                task.execute()
        
    # if no tasks were executed, then alert the user that nothing
    # needed to be run
    else:
        print("No tasks were run in the workflow defined in '%s'" % (
            task_graph.config_path,
        ))
        
    # otherwise, we need to recalculate hashes for everything that is
    # out of sync
    task_graph.save_state()
