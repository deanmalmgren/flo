from .parser import find_config_path, load_task_graph

def execute():
    """Execute the task workflow.
    """

    # look for workflow configuration file
    config_path = find_config_path()
    
    # read in tasks from workflow configuration file
    # and infer dependency graph of tasks
    task_graph = load_task_graph(config_path)
    task_graph.load_state()

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
        print("No tasks were run in the workflow defined in '%s'" % config_path)
        
    # otherwise, we need to recalculate hashes for everything that is
    # out of sync
    task_graph.save_state()
