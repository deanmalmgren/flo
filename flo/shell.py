"""Module for executing commands on the command line
"""
import subprocess
import sys
import threading

from . import exceptions
from . import logger as flo_logger


def log_output(stream, block_size=1):
    """This function logs the output from the subprocess'ed command by
    reading the output stream in small blocks of size `block_size`
    bytes to properly handle backspacing outputs (issue #53)
    """
    logger = flo_logger.get()
    while True:
        data = stream.read(block_size)
        if not data:
            break
        logger.write(data)
    stream.close()


def run(directory, command):
    """Run the specified shell command using Fabric-like behavior."""

    # combine stderr and stdout output when running command so we can
    # stream output to the logger for output to terminal and file
    # simultaneously
    wrapped_command = "cd %s && %s" % (directory, command)
    pipe = subprocess.Popen(
        wrapped_command, shell=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )

    # this uses threading to capture the output in real time in a
    # non-blocking way and use the log_output function to report the
    # output using the logging module. This framework takes
    # inspiration from http://stackoverflow.com/a/4985080/564709
    thread = threading.Thread(target=log_output, args=(pipe.stdout,))
    thread.daemon = True
    thread.start()
    thread.join()
    pipe.wait()

    # if pipe is busted, raise an error
    if pipe.returncode != 0:
        raise exceptions.ShellError(pipe.returncode)
