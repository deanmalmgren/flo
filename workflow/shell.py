"""Module for executing commands on the command line
"""
import subprocess
import sys
import logging

from . import exceptions

def run(directory, command):
    """Run the specified shell command using Fabric-like behavior"""
    # TODO get logging to work in here, too
    wrapped_command = "cd %s && %s" % (directory, command)
    pipe = subprocess.Popen(
        wrapped_command, shell=True, 
        stdout=sys.stdout, stderr=sys.stderr,
    )
    pipe.communicate()
    if pipe.returncode != 0:
        raise exceptions.ShellError(pipe.returncode)
