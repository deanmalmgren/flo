"""This module sets up logging to split output to terminal and to
file, which can be convenient for inspecting long-running jobs and for
sending notifications with useful content
"""

import sys

from .colors import colorless


# NOTE: using the logging module caused all kinds of problems with
# backspacing output and whatnot. This is a much simpler solution and
# achieves exactly what we want, albeit not using the standard
# library. If you have other ideas for how to do this, check out the
# code before issue #53 was resolved.
# class Logger(file):
class Logger():
    """Log output to stdout in color and to a log file in plain text.
    """
    log_file = None

    def __init__(self, task_graph):
        self.log_file = open(task_graph.abs_log_path, 'w')

    def write(self, content):
        if isinstance(content, bytes):
            content = content.decode()
        sys.stdout.write(content)
        sys.stdout.flush()
        self.log_file.write(colorless(content))

    def info(self, content):
        self.write(content + '\n')

    def close(self):
        self.log_file.close()

# _logger is a singleton instance of the logger that is a local cache
# of the one and only logger instance for all TaskGraphs. This is
# necessary in the event that a subgraph is selected.
_logger = None


def get():
    global _logger
    return _logger


def configure(task_graph):
    global _logger
    if _logger is not None:
        return _logger
    _logger = Logger(task_graph)
    return _logger
