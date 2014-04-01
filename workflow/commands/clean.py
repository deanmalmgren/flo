import time
from distutils.util import strtobool

from ..parser import load_task_graph
from ..colors import red, green

def clean(task_id=None, force=False, export=False, pause=0.5, 
          include_internals=False, **kwargs):
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

    # XXXX LEFT OFF HERE. FIND WAY TO INCLUDE ALL OF THE INTERNALS IN
    # A SMART WAY HERE. THIS SHOULD ALERT USER IF --force IS NOT USED
    # AND ALSO REMOVE THE CORRESPONDING CONTENT AFTER THE FACT

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

    # now actually clean things up with the TaskGraph.clean method
    task_graph.clean(export=export, task_list=task_list, 
                     include_internals=include_internals)

    # mark the task_graph as completing successfully to send the
    # correct email message
    task_graph.successful = True
