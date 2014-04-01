from ..parser import load_task_graph, get_available_archives
from ..exceptions import ConfigurationNotFound

def command(restore=False, exclude_internals=False, **kwargs):
    """Interact with archives of the workflow, by either backing it up or
    restoring it from a previous backup.
    """
    task_graph = load_task_graph()
    if restore:
        task_graph.restore_archive(restore)
    else:
        task_graph.write_archive(exclude_internals=exclude_internals)

    # REFACTOR TODO: IS THIS NECESSARY IF NOTIFY IS ONLY USED WITH run
    # COMMAND? see REFACTOR TODO in __init__.py
    #
    # mark the task_graph as completing successfully to send the
    # correct email message
    task_graph.successful = True

def add_to_parser(subparsers):
    try:
        available_archives = get_available_archives()
    except ConfigurationNotFound:
        available_archives = []
    parser = subparsers.add_parser(
        'archive', 
        help='Create and restore backup archives of data analysis workflows',
    )
    parser.add_argument(
        '--restore',
        choices=available_archives,
        default=False,
        nargs='?',
        help="Restore the state of the workflow."
    )
    parser.add_argument(
        '--exclude-internals',
        action="store_true",
        help="exclude internals in the .workflow/ directory from archive",
    )
    parser.set_defaults(func=command)
