import sys
import os
import subprocess
import time
import hashlib

import jinja2

from .exceptions import InvalidTaskDefinition, ElementNotFound
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
            raise InvalidTaskDefinition(
                "every task must define a `creates`"
            )
        if self.command is None:
            raise InvalidTaskDefinition(
                "every task must define a `command`"
            )

        # get the root directory
        # 
        # TODO: this probably isn't the best place to put this as it
        # computes the root directory for *every* task. While this
        # calculation is very fast, its certainly unnecessary
        self.root_directory = utils.get_root_directory()

        # render the jinja template for the command
        self.command = self.render_command_template()

    def calculate_hash(self, stream, block_size=2**20):
        """Read in a stream in relatively small `block_size`s to make sure we
        won't have memory problems on BIG DATA streams.
        http://stackoverflow.com/a/1131255/564709
        """
        stream_hash = hashlib.sha1()
        while True:
            data = stream.read(block_size)
            if not data:
                break
            stream_hash.update(data)
        return stream_hash.hexdigest()

    def hash_in_sync(self, element):
        """Check the stored hash of this element compared with the current
        hash of this element. If they are the same, then this element
        is in_sync.
        """

        # if the element is None type (for example, when you only
        # specify a `creates` and a `command`, but no `depends`),
        # consider this in sync at this stage. 
        if element is None:
            return True

        # Get the stored hash value if it exists. If it doesn't exist,
        # then automatically consider this element out of sync
        stored_hash = None

        # Get the current hash of this element. If the element does
        # not exist, throw an error.
        # 
        # TODO: This should be able to accomodate files stored on the
        # filesystem AS WELL AS databases, database tables, cloud storage, etc.
        current_hash = None
        element_path = os.path.join(self.root_directory, element)
        if os.path.exists(element_path):
            with open(element_path) as stream:
                current_hash = self.calculate_hash(stream)

        if current_hash is None:
            raise ElementNotFound(element)

        # element is in_sync if the stored and current hashes are the same
        return stored_hash == current_hash

    def in_sync(self):
        """Test whether this task is in sync with the stored state and
        needs to be executed
        """
        # if the creates doesn't exist, its not in sync and the task
        # must be executed
        if not os.path.exists(os.path.join(self.root_directory, self.creates)):
            return False

        # if any of the dependencies are out of sync, then this task
        # must be executed
        if isinstance(self.depends, (list, tuple)):
            for dep in self.depends:
                if not self.hash_in_sync(dep):
                    return False
        elif not self.hash_in_sync(self.depends):
            return False

        # if the data about this task is out of sync, then this task
        # must be executed
        #
        # TODO: check the hash of this task

        # otherwise, its in sync
        return True
        
    def execute(self, command=None):
        """Run the specified task from the root of the workflow"""

        # execute a sequence of commands by recursively calling this
        # method
        command = command or self.command
        if isinstance(command, (list, tuple)):
            for cmd in command:
                self.execute(cmd)
            return

        # start a timer so we can keep track of how long this task
        # executes. Its important that we're timing watch time, not
        # CPU time
        t = time.time()

        # if its not a list or a tuple, then this string should be
        # executed. Update the user on our progress so far, be sure to
        # change to the root directory of the workflow, and execute
        # the command. This takes inspiration from how
        # fabric.operations.local works http://bit.ly/1dQEgjl
        print(command)
        sys.stdout.flush()
        wrapped_command = "cd %s && %s" % (self.root_directory, command)
        pipe = subprocess.Popen(
            wrapped_command, shell=True, stdout=sys.stdout, stderr=sys.stderr
        )
        (stdout, stderr) = pipe.communicate()
        if pipe.returncode != 0:
            sys.exit(pipe.returncode)

        # stop the clock and alert the user to the clock time spent
        # exeucting the task
        self.deltat = time.time() - t
        if self.deltat < 10 * 60: # 10 minutes
            deltat_str = "%.2f" % (self.deltat) + " s" 
        elif self.deltat < 2 * 60 * 60: # 2 hours
            deltat_str = "%.2f" % (self.deltat / 60) + " m"
        elif self.deltat < 2 * 60 * 60 * 24: # 2 days
            deltat_str = "%.2f" % (self.deltat / 60 / 60) + " h"
        else:
            deltat_str = "%.2f" % (self.deltat / 60 / 60 / 24) + " d"
        print("%79s" % deltat_str)


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
