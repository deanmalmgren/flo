import time
from distutils.util import strtobool

from ..parser import load_task_graph, get_available_tasks
from ..colors import red, green
from ..exceptions import ConfigurationNotFound

def command(task_id=None, force=False, export=False, pause=0.5, 
          include_internals=False, **kwargs):
    """Remove all `creates` targets defined in workflow. If a task_id is
    specified, only remove that target.
    """
    task_graph = load_task_graph()

    # if a task_id is specified, only remove this particular
    # task. otherwise, remove everything.
    task_list = task_graph.task_list
    if task_id is not None:
        task_list = [task_graph.task_dict[task_id]]

    # REFACTOR TODO: put this in a TaskGraph method 
    #
    # print a warning message before removing all tasks. Briefly
    # pause to make sure user sees the message at the top.
    if not (force or export):
        task_graph.logger.info(red(
            "Please confirm that you want to delete the following files."
        ))
        time.sleep(pause)
        for task in task_list:
            if not task.is_pseudotask():
                task_graph.logger.info(task.creates_message())
        if include_internals:
            task_graph.logger.info(green(task_graph.internals_path))
        yesno = raw_input(red("Delete aforementioned files? [Y/n] "))
        if yesno == '':
            yesno = 'y'
        if not strtobool(yesno):
            return

    task_graph.clean(export=export, task_list=task_list, 
                     include_internals=include_internals)

    # REFACTOR TODO: IS THIS NECESSARY IF NOTIFY IS ONLY USED WITH run
    # COMMAND? see REFACTOR TODO in __init__.py
    #
    # mark the task_graph as completing successfully to send the
    # correct email message
    task_graph.successful = True

def add_to_parser(subparsers):
    try:
        available_tasks = get_available_tasks()
    except ConfigurationNotFound:
        available_tasks = []
    parser = subparsers.add_parser(
        'clean', 
        help='clean up the workflow',
    )
    parser.add_argument(
        'task_id',
        metavar='TASK',
        type=str,
        choices=available_tasks,
        nargs='?', # '*', this isn't working for some reason
        help='Specify a particular task to clean rather than all of them.',
    )
    parser.add_argument(
        '-f', '--force',
        action="store_true",
        help="Remove all `creates` targets in workflow without confirmation.",
    )
    parser.add_argument(
        '--include-internals',
        action="store_true",
        help="Remove all files in the .workflow/ directory.",
    )
    parser.set_defaults(func=command)
