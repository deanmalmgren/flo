import sys
import os
import subprocess
import time
import hashlib
import csv

import jinja2

from .exceptions import InvalidTaskDefinition, ElementNotFound
from . import colors

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

        # initially set the graph attribute as None. This is
        # configured when the Task is added to the graph
        self.graph = None

        # render the jinja template for the command
        self.command = self.render_command_template()

    @property
    def id(self):
        """Canonical way to identify this Task"""
        return self.alias or self.creates

    @property
    def root_directory(self):
        """Easy access to the graph's root_directory, which is stored once for
        every task"""
        return self.graph.root_directory

    def get_stream_state(self, stream, block_size=2**20):
        """Read in a stream in relatively small `block_size`s to make sure we
        won't have memory problems on BIG DATA streams.
        http://stackoverflow.com/a/1131255/564709
        """
        state = hashlib.sha1()
        while True:
            data = stream.read(block_size)
            if not data:
                break
            state.update(data)
        return state.hexdigest()

    def get_element_state(self, element):
        """Get the current state of this element. If the element does
        not exist, throw an error.
        
        TODO: This should be able to accomodate files stored on the
        filesystem AS WELL AS databases, database tables, cloud
        storage, etc. Can address this with protocols like
        mysql:dbname/table or mongo:db/collection
        """
        state = None

        # for filesystem protocols, dereference any soft links that
        # the element may point to and calculate the state from
        element_path = os.path.realpath(
            os.path.join(self.root_directory, element)
        )
        if os.path.exists(element_path):
            if os.path.isfile(element_path):
                with open(element_path) as stream:
                    state = self.get_stream_state(stream)
            elif os.path.isdir(element_path):
                state_hash = hashlib.sha1()
                for root, directories, filenames in os.walk(element_path):
                    for filename in filenames:
                        with open(os.path.join(root, filename)) as stream:
                            state_hash.update(self.get_stream_state(stream))
                state = state_hash.hexdigest()
                
            else:
                raise NotImplementedError((
                    "file a feature request to support this type of "
                    "element "
                    "https://github.com/deanmalmgren/data-workflow/issues"
                ))
        return state

    def state_in_sync(self, element):
        """Check the stored state of this element compared with the current
        state of this element. If they are the same, then this element
        is in_sync.
        """

        # if the element is None type (for example, when you only
        # specify a `creates` and a `command`, but no `depends`),
        # consider this in sync at this stage. 
        if element is None:
            return True

        # Get the stored state value if it exists. If it doesn't exist,
        # then automatically consider this element out of sync
        stored_state = self.graph.before_element_states.get(element, None)

        # get the current state of the file just before runtime
        current_state = self.get_element_state(element)

        # store the after element state here. If its none, its updated
        # at the very end
        self.graph.after_element_states[element] = current_state

        # element is in_sync if the stored and current states are the same
        return stored_state == current_state

    def in_sync(self):
        """Test whether this task is in sync with the stored state and
        needs to be executed
        """
        in_sync = True

        # if the creates doesn't exist, its not in sync and the task
        # must be executed
        if not os.path.exists(os.path.join(self.root_directory, self.creates)):
            in_sync = False

        # if any of the dependencies are out of sync, then this task
        # must be executed
        if isinstance(self.depends, (list, tuple)):
            for dep in self.depends:
                if not self.state_in_sync(dep):
                    in_sync = False # but still iterate
        elif not self.state_in_sync(self.depends):
            return False

        # if the data about this task is out of sync, then this task
        # must be executed
        #
        # TODO: check the state of this task

        # otherwise, its in sync
        return in_sync

    def run(self, command):
        """Run the specified shell command using Fabric-like behavior"""
        wrapped_command = "cd %s && %s" % (self.root_directory, command)
        pipe = subprocess.Popen(
            wrapped_command, shell=True, 
            stdout=sys.stdout, stderr=sys.stderr
        )
        pipe.communicate()
        if pipe.returncode != 0:
            sys.exit(pipe.returncode)

    def clean(self):
        """Remove the specified target"""
        self.run("rm -rf %s" % self.creates)
        print("removed %s" % self.creates_message())

    def execute(self, command=None):
        """Run the specified task from the root of the workflow"""

        # start of task execution
        start_time = None
        if command is None:

            # useful message about starting this task and what it is
            # called so users know how to re-call this task if they
            # notice something fishy during execution.
            print(self.creates_message())

            # start a timer so we can keep track of how long this task
            # executes. Its important that we're timing watch time, not
            # CPU time
            start_time = time.time()

        # execute a sequence of commands by recursively calling this
        # method
        command = command or self.command
        if isinstance(command, (list, tuple)):
            for cmd in command:
                self.execute(cmd)

        # if its not a list or a tuple, then this string should be
        # executed. Update the user on our progress so far, be sure to
        # change to the root directory of the workflow, and execute
        # the command. This takes inspiration from how
        # fabric.operations.local works http://bit.ly/1dQEgjl
        else:
            print(self.command_message(command=command))
            sys.stdout.flush()
            self.run(command)

        # stop the clock and alert the user to the clock time spent
        # exeucting the task
        if start_time:
            self.duration = time.time() - start_time
            print(self.duration_message())

            # store the duration on the graph object
            self.graph.task_durations[self.id] = self.duration

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

    def duration_message(self, color=colors.blue):
        msg = "%79s" % self.graph.duration_string(self.duration)
        if color:
            msg = color(msg)
        return msg

    def creates_message(self, color=colors.green):
        msg = self.creates
        if self.alias:
            msg += " (%s)" % self.alias
        if color:
            msg = color(msg)
        return msg

    def command_message(self, command=None, color=colors.bold_white):
        command = command or self.command
        if isinstance(command, (list, tuple)):
            msg = []
            for subcommand in command:
                msg.append(self.command_message(command=subcommand, color=color))
            return '\n'.join(msg)
        msg = "|-> " + command
        if color:
            msg = color(msg)
        return msg

class TaskGraph(object):
    """Simple graph implementation of a list of task nodes"""

    # relative location of various storage locations
    state_path = os.path.join(".workflow", "state.csv")
    duration_path = os.path.join(".workflow", "duration.csv")

    def __init__(self, config_path):
        self.tasks = []

        # store paths once for all tasks.
        self.config_path = config_path
        self.root_directory = os.path.dirname(config_path)

        # Store the local in_sync state which doesn't change during a
        # run. These dictionaries store {element: state} pairs for
        # every element that is in this workflow. The
        # before_element_states read in the state stored locally in
        # .workflow/storage.tsv and the after_element_states read the
        # state calculated just before that element is run. At the end
        # of the workflow, the after_element_states are dumped to
        # storage as necessary. 
        self.before_element_states = {}
        self.after_element_states = {}

        # store the time that this task takes
        self.task_durations = {}

    def add(self, task):
        self.tasks.append(task)
        task.graph = self

        # TODO: when tasks are added, make sure the creates/aliases
        # are unique so there aren't any problems deciphering
        # information. Can take care of this when we start to worry
        # about task dependencies

    def __iter__(self):
        # TODO: when we figure out dependency tree, probably should do
        # something considerably different here
        return iter(self.tasks)

    def duration_string(self, duration):
        if duration < 10 * 60: # 10 minutes
            return "%.2f" % (duration) + " s" 
        elif duration < 2 * 60 * 60: # 2 hours
            return "%.2f" % (duration / 60) + " m"
        elif duration < 2 * 60 * 60 * 24: # 2 days
            return "%.2f" % (duration / 60 / 60) + " h"
        else:
            return "%.2f" % (duration / 60 / 60 / 24) + " d"

    def duration_message(self, tasks=None, color=colors.blue):
        # TODO: when we implement the dependency graph, this can also
        # give an upper bound on the duration time, which would also
        # be very helpful. by starting at the seed tasks, we can
        # assume all other downstream tasks will also need to be run.
        tasks = tasks or self.tasks
        duration = 0.0
        n_unknown = 0
        for task in tasks:
            try:
                duration += self.task_durations[task.id]
            except KeyError:
                n_unknown += 1
        msg = ''
        if n_unknown:
            msg += "%d new tasks with unknown durations.\n" % n_unknown
        msg += "At least %d tasks need to be executed,\n" % (
            len(tasks) - n_unknown, 
        )
        msg += "which will take at least %s" % (
            self.duration_string(duration),
        )
        return color(msg)

    @property
    def abs_state_path(self):
        """Convenience property for accessing state storage location"""
        return os.path.join(self.root_directory, self.state_path)

    @property
    def abs_duration_path(self):
        """Convenience property for accessing duration storage location"""
        return os.path.join(self.root_directory, self.duration_path)

    def _read_from_storage(self, dictionary, storage_location):
        if os.path.exists(storage_location):
            with open(storage_location) as stream:
                reader = csv.reader(stream)
                for row in reader:
                    dictionary[row[0]] = row[1]

    def _write_to_storage(self, dictionary, storage_location):
        directory = os.path.dirname(storage_location)
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(storage_location, 'w') as stream:
            writer = csv.writer(stream)
            for item in dictionary.iteritems():
                writer.writerow(item)

    def load_state(self):
        """Load the states of all elements (files, databases, etc). If the
        state file hasn't been stored yet, nothing happens. This also
        loads the duration statistics on this task.

        """
        self._read_from_storage(self.before_element_states, self.abs_state_path)
        self._read_from_storage(self.task_durations, self.abs_duration_path)

        # typecast the task_durations
        for task_id, duration in self.task_durations.iteritems():
            self.task_durations[task_id] = float(duration)

    def save_state(self):
        """Save the states of all elements (files, databases, etc). If the
        state file hasn't been stored yet, it creates a new one.
        """

        # before saving the after_element_states, replace any None
        # values with a recalculated state. This happens, for example,
        # when a `creates` target is made the first time it executes
        # the task. At this point, every target should have a state!
        # 
        # TODO: this is a bit of a hack to be able to use Task's
        # get_element_state method. Should probably find a better
        # place to organize this code so we don't have to do that
        dummy_task = Task(creates="creates", command="command")
        dummy_task.graph = self
        for element, state in self.after_element_states.iteritems():
            state = dummy_task.get_element_state(element)
            if state is None:
                raise ElementNotFound(element)
            self.after_element_states[element] = state

        self._write_to_storage(self.after_element_states, self.abs_state_path)
        self._write_to_storage(self.task_durations, self.abs_duration_path)
