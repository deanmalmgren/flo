from ..parser import load_task_graph

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
