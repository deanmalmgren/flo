"""This module sets up logging to split output to terminal and to
file, which can be convenient for inspecting long-running jobs and for
sending notifications with useful content
"""

import logging
import sys

from .colors import colorless

class ColorlessFileHandler(logging.FileHandler):
    def emit(self, record):
        record.msg = colorless(record.msg)
        return super(ColorlessFileHandler, self).emit(record)

def configure(task_graph):
    logger = logging.getLogger('workflow')
    logger.setLevel(logging.DEBUG)

    # create file handler and a console handler that logs to stdout
    file_handler = ColorlessFileHandler(task_graph.abs_log_path, mode='w')
    console_handler = logging.StreamHandler(sys.stdout)

    # set the logging levels on these handlers
    file_handler.setLevel(logging.DEBUG)
    console_handler.setLevel(logging.DEBUG)

    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # add the handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)


    return logger

