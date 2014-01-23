from .parser import find_config_filename, load_task_graph

def main():

    # look for workflow configuration file
    config_filename = find_config_filename()
    
    # read in tasks from workflow configuration file
    # and infer dependency graph of tasks
    task_graph = load_task_graph(config_filename)

    # iterate through every task in the task graph and execute every
    # task that is out of sync with our last stored state
    for task in task_graph:
        if task.out_of_sync():
            task.execute()
