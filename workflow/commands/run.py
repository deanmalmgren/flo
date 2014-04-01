import os
import sys

from ..parser import load_task_graph, get_available_tasks
from ..exceptions import ShellError, ConfigurationNotFound

def command(task_id=None, force=False, dry_run=False, export=False, **kwargs):
    """Execute the task workflow.
    """
    task_graph = load_task_graph()

    # REFACTOR TODO: this function is almost certainly overcommented
    # and should be broken into separate methods in a TaskGraph

    # TODO: does this introduce bugs in the .workflow/state.csv file?
    # 
    # if any tasks are specified, limit the task graph to only those
    # tasks that are required to create the specified tasks
    if task_id is not None:
        task_graph = task_graph.subgraph_needed_for([task_id])

    # iterate through every task in the task graph and find the set of
    # tasks that have to be executed. we do this first so we can alert
    # the user as to how long this workflow will take. breadth first
    # search on entire task graph to make sure the out_of_sync_tasks
    # are created in the appropriate order for subsequent steps.
    out_of_sync_tasks = []
    for task in task_graph.iter_bfs():

        # regardless of whether we force the execution of the command,
        # run the in_sync method, which calculates the state of the
        # task and all `creates` / `depends` elements
        if not task.is_pseudotask() and (force or not task.in_sync()):
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
            if not task.is_pseudotask() and (force or not task.in_sync()):
                if not (dry_run or export):
                    try:
                        task.execute()
                    except (KeyboardInterrupt, ShellError), e:
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
        
    # if no tasks needed to be executed, then alert the user.
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

def add_to_parser(subparsers):
    try:
        available_tasks = get_available_tasks()
    except ConfigurationNotFound:
        available_tasks = []

    parser = subparsers.add_parser(
        'run', 
        help='Run the workflow.',
    )
    parser.add_argument(
        'task_id',
        metavar='TASK',
        type=str,
        choices=available_tasks,
        nargs='?', # '*', this isn't working for some reason
        help='Specify a particular task to run.',
    )
    parser.add_argument(
        '-f', '--force',
        action="store_true",
        help="Rerun entire workflow, regardless of task state.",
    )
    parser.add_argument(
        '-d', '--dry-run',
        action="store_true",
        help=(
            "Do not run workflow, just report which tasks would be run and how "
            "long it would take."
        ),
    )
    parser.add_argument(
        '-e', '--export',
        action="store_true",
        help="Export shell script instead of running the workflow.",
    )
    parser.add_argument(
        '--notify',
        type=str,
        metavar='EMAIL',
        nargs=1,
        help='Specify an email address to notify on completion.',
    )
    parser.set_defaults(func=command)
