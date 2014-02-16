"""Module for executing commands on the command line
"""
import subprocess
import sys

def run(directory, command):
    """Run the specified shell command using Fabric-like behavior"""
    wrapped_command = "cd %s && %s" % (directory, command)
    pipe = subprocess.Popen(
        wrapped_command, shell=True, 
        stdout=sys.stdout, stderr=sys.stderr
    )
    pipe.communicate()
    if pipe.returncode != 0:
        sys.exit(pipe.returncode)
