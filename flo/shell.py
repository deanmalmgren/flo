"""Module for executing commands on the command line
"""
import subprocess
import sys
import logging
import threading

from . import exceptions


def log_output(stream):
    # this function logs the output from the subprocess'ed command.
    #
    # TODO: this works for all outputs that do not backspace. Note
    # what happens when you run the workflow in examples/reuters-tfidf
    # when curl is running
    logger = logging.getLogger('flo')
    for line in iter(stream.readline, ''):
        logger.info(line.rstrip('\n'))
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
