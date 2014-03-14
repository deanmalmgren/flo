import os
import time
from distutils.util import strtobool
import sys

from .parser import load_task_graph
from . import colors
from . import exceptions

def clean(task_id=None, force=False, export=False, pause=0.5, **kwargs):
    """Remove all `creates` targets defined in workflow. If a task_id is
    specified, only remove that target.
    """

    # load the task graph
    task_graph = load_task_graph()

    # if a task_id is specified, only remove this particular
    # task. otherwise, remove everything.
    task_list = task_graph.task_list
    if task_id is not None:
        task_list = [task_graph.task_dict[task_id]]

    # print a warning message before removing all tasks. Briefly
    # pause to make sure user sees the message at the top.
    if not (force or export):
        task_graph.logger.info(colors.red(
            "Please confirm that you want to delete the following files."
        ))
        time.sleep(pause)
        for task in task_list:
            if not task.is_pseudotask():
                task_graph.logger.info(task.creates_message())
        yesno = raw_input(colors.red("Delete aforementioned files? [Y/n] "))
        if yesno == '':
            yesno = 'y'
        if not strtobool(yesno):
            return

    # now actually clean things up with the TaskGraph.clean method
    task_graph.clean(export=export, task_list=task_list)

    # mark the task_graph as completing successfully to send the
    # correct email message
    task_graph.successful = True

def execute(task_id=None, force=False, dry_run=False, export=False, **kwargs):
    """Execute the task workflow.
    """

    # load the task graph
    task_graph = load_task_graph()

    # if any tasks are specified, limit the task graph to only those
    # tasks that are required to create the specified tasks
    if task_id is not None:
        task_graph = task_graph.subgraph_needed_for([task_id])

    # iterate through every task in the task graph and find the set of
    # tasks that have to be executed. we do this first so we can alert
    # the user as to how long this workflow will take. use breadth
    # first search on entire task graph to make sure the
    # out_of_sync_tasks are created in the appropriate order for
    # subsequent steps.
    out_of_sync_tasks = []
    for task in task_graph.iter_bfs():

        # regardless of whether we force the execution of the command,
        # run the in_sync method, which calculates the state of the
        # task and all `creates` / `depends` elements
        if (not task.in_sync() or force) and not task.is_pseudotask():
            out_of_sync_tasks.append(task)

    # report the minimum amount of time this will take to execute and
    # execute all tasks
    if out_of_sync_tasks:
        if export:
            print("cd %s" % task_graph.root_directory)
        else:
            task_graph.logger.info(
                task_graph.duration_message(out_of_sync_tasks)
            )
        for task in task_graph.iter_bfs(out_of_sync_tasks):
            # We unfortunately need (?) to re-run in_sync here in case
            # things change during the course of a run. This is not
            # ideal but makes it possible to estimate the duration of
            # a workflow run, which is pretty valuable
            if (not task.in_sync() or force) and not task.is_pseudotask():
                if not (dry_run or export):
                    try:
                        task.execute()
                    except (KeyboardInterrupt, exceptions.ShellError), e:
                        # on keyboard interrupt or error on executing
                        # a specific step, make sure all previously
                        # run tasks have their state properly stored
                        # and make sure re-running the workflow will
                        # rerun the task that was underway. we do this
                        # by saving the state of everything but
                        # overridding the state of the creates
                        # resource for this task before exiting
                        task_graph.save_state(
                            override_resource_states={task.name:''},
                        )
                        sys.exit(getattr(e, 'exit_code', 1))
                elif dry_run:
                    task_graph.logger.info(str(task))
                elif export:
                    task_graph.logger.info(
                        task.command_message(color=None, pre="")
                    )
        
    # if no tasks were executed, then alert the user that nothing
    # needed to be run
    else:
        task_graph.logger.info(
            "No tasks are out of sync in the workflow defined in '%s'" % (
                os.path.relpath(task_graph.config_path, os.getcwd())
            )
        )
        
    # otherwise, we need to recalculate hashes for everything that is
    # out of sync
    if not (dry_run or export):
        task_graph.save_state()

    # mark the task_graph as completing successfully to send the
    # correct email message
    task_graph.successful = True

def archive(restore=False, exclude_internals=False, **kwargs):
    """Interact with archives of the workflow, by either backing it up or
    restoring it from a previous backup.
    """
    
    # load in the task_graph
    task_graph = load_task_graph()

    # find an archive to restore and restore it. This should probably
    # ask the user to confirm which archive to restore before doing
    # anything.
    if restore:
        task_graph.restore_archive(restore)

    # create an ensemble of filenames that need to be archived
    else:
        task_graph.write_archive(exclude_internals=exclude_internals)


    # mark the task_graph as completing successfully to send the
    # correct email message
    task_graph.successful = True
