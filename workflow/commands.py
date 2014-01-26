import os
import time
from distutils.util import strtobool

from .parser import load_task_graph
from . import colors

def clean(force=False, export=False, pause=0.5):
    """Remove all `creates` targets defined in workflow
    """

    # load the task graph
    task_graph = load_task_graph()

    # print a warning message before removing all tasks. Briefly
    # pause to make sure user sees the message at the top.
    if not (force or export):
        print(colors.red(
            "Please confirm that you want to delete the following files."
        ))
        time.sleep(pause)
        for task in task_graph.task_list:
            print(task.creates_message())
        yesno = raw_input(colors.red("Delete aforementioned files? [Y/n] "))
        if yesno == '':
            yesno = 'y'
        if not strtobool(yesno):
            return

    # for every task in the task graph, remove the corresponding
    # `creates` targets
    if export:
        print("cd %s" % task_graph.root_directory)
    task_graph.clean(export=export)

def execute(task_id=None, force=False, dry_run=False, export=False):
    """Execute the task workflow.
    """

    # load the task graph
    task_graph = load_task_graph()

    # if any tasks are specified, limit the task graph to only those
    # tasks that are required to create the specified tasks
    if task_id is not None:
        task_graph = task_graph.subgraph_needed_for([task_id])
        print len(task_graph.task_list)

    # iterate through every task in the task graph and find the set of
    # tasks that have to be executed. we do this first so we can alert
    # the user as to how long this workflow will take
    out_of_sync_tasks = []
    for task in task_graph.task_list:

        # regardless of whether we force the execution of the command,
        # run the in_sync method, which calculates the state of the
        # task and all `creates` / `depends` elements
        if not task.in_sync() or force:
            out_of_sync_tasks.append(task)

    # report the minimum amount of time this will take to execute and
    # execute all tasks
    if out_of_sync_tasks:
        if export:
            print("cd %s" % task_graph.root_directory)
        else:
            print(task_graph.duration_message(out_of_sync_tasks))
        for task in task_graph.iter_bfs(out_of_sync_tasks):
            # We unfortunately need (?) to re-run in_sync here in case
            # things change during the course of a run. This is not
            # ideal but makes it possible to estimate the duration of
            # a workflow run, which is pretty valuable
            if not task.in_sync() or force:
                if not (dry_run or export):
                    task.execute()
                elif dry_run:
                    print(task)
                elif export:
                    print(task.command_message(color=None, pre=""))
        
    # if no tasks were executed, then alert the user that nothing
    # needed to be run
    else:
        print("No tasks were run in the workflow defined in '%s'" % (
            os.path.relpath(task_graph.config_path, os.getcwd())
        ))
        
    # otherwise, we need to recalculate hashes for everything that is
    # out of sync
    if not (dry_run or export):
        task_graph.save_state()

def archive(backup=False, restore=False):
    """Interact with archives of the workflow, by either backing it up or
    restoring it from a previous backup.
    """
    pass

