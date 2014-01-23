import sys
import os
import subprocess

import jinja2

from . import exceptions
from . import utils

class Task(object):

    def __init__(self, creates=None, depends=None, alias=None, command=None, 
                 **kwargs):
        self.creates = creates
        self.depends = depends
        self.command = command
        self.alias = alias

        # remember other attributes of this Task for rendering
        # purposes below
        self.command_attrs = kwargs
        self.command_attrs.update({
            'creates': self.creates,
            'depends': self.depends,
            'alias': self.alias,
        })

        # quick type checking to make sure the tasks in the
        # configuration file are valid
        if self.creates is None:
            raise exceptions.InvalidTaskDefinition(
                "every task must define a `creates`"
            )
        if self.command is None:
            raise exceptions.InvalidTaskDefinition(
                "every task must define a `command`"
            )

        # render the jinja template for the command
        self.command = self.render_command_template()

    def in_sync(self):
        """Test whether this task is in sync with the stored state and
        needs to be executed
        """
        return False

    def execute(self, command=None):
        """Run the specified task from the root of the workflow"""

        # execute a sequence of commands by recursively calling this
        # method
        command = command or self.command
        if isinstance(command, (list, tuple)):
            for cmd in command:
                self.execute(cmd)
            return

        # if its not a list or a tuple, then this string should be
        # executed. Update the user on our progress so far, be sure to
        # change to the root directory of the workflow, and execute
        # the command. This takes inspiration from how
        # fabric.operations.local works http://bit.ly/1dQEgjl
        print(command)
        sys.stdout.flush()
        wrapped_command = "cd %s && %s" % (utils.get_root_directory(), command)
        pipe = subprocess.Popen(
            wrapped_command, shell=True, stdout=sys.stdout, stderr=sys.stderr
        )
        (stdout, stderr) = pipe.communicate()
        if pipe.returncode != 0:
            sys.exit(pipe.returncode)

    def render_command_template(self, command=None):
        """Uses jinja template syntax to render the command from the other
        data specified in the YAML file
        """

        # if command is a list, render recursively
        command = command or self.command
        if isinstance(command, (list, tuple)):
            return [self.render_command_template(cmd) for cmd in command]

        # otherwise, need to render the template with Jinja2
        env = jinja2.Environment()
        template = env.from_string(command)
        return template.render(self.command_attrs)

class TaskGraph(object):
    """Simple graph implementation of a list of task nodes"""

    def __init__(self):
        self.tasks = []

    def add(self, task):
        self.tasks.append(task)

    def __iter__(self):
        return iter(self.tasks)
