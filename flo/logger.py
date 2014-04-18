"""This module sets up logging to split output to terminal and to
file, which can be convenient for inspecting long-running jobs and for
sending notifications with useful content
"""

import logging
import sys

from .colors import colorless

# _logger is a singleton instance of the logger that is a local cache
# of the one and only logger instance for all TaskGraphs. This is
# necessary in the event that a subgraph is selected.
_logger = None


class ColorlessFileHandler(logging.FileHandler):
    def emit(self, record):
        record.msg = colorless(record.msg)
        return super(ColorlessFileHandler, self).emit(record)


def configure(task_graph):
    global _logger
    if _logger is not None:
        return _logger

    _logger = logger = logging.getLogger('flo')
    logger.setLevel(logging.DEBUG)

    # create file handler and a console handler that logs to stdout
    console_handler = logging.StreamHandler(sys.stdout)
    file_handler = ColorlessFileHandler(task_graph.abs_log_path, mode='w')

    # set the logging levels on these handlers
    console_handler.setLevel(logging.DEBUG)
    file_handler.setLevel(logging.DEBUG)

    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # add the handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
