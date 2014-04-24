import sys
import os

from fabric.api import local, lcd #, hide

example_root = sys.argv[1]

cmd = "flo status -f"
start = "data/x_y.dat"
end = "data/x_cdf.dat"

def get_tasks(start,end):
    command = cmd
    if start:
        command += " --start-at=%s"%start
    if end:
        command += " %s"%end
    # with hide("running"):
    return local(command, capture=True).split("\n")[2:]

with lcd(os.path.join(example_root, "model-correlations")):
    tasks = get_tasks(start,end)

    msg = "subgraph had %s tasks"
    assert start in tasks[0], "did not start where it was supposed to"
    assert end in tasks[-1], "did not end where it was supposed to"
    assert len(get_tasks(None,None)) > len(tasks), msg%"all of the"
    assert len(get_tasks(start,None)) > len(tasks), msg%"too many"
    assert len(get_tasks(None,end)) > len(tasks), msg%"too many"
