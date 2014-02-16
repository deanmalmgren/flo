import sys
import os
import time
import hashlib
import csv
import StringIO
import collections
import datetime
import glob

import jinja2

from .exceptions import InvalidTaskDefinition, ElementNotFound, NonUniqueTask
from . import colors
from . import shell

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

        # create some data structures for storing the set of tasks on
        # which this task depends (upstream_tasks) on what depends on
        # it (downstream_tasks)
        self.downstream_tasks = set()
        self.upstream_tasks = set()        

        # save the original command strings in _command for checking
        # the state of this command and render the jinja template for
        # the command
        self._command = self.command
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

    def add_task_dependency(self, depends_on):
        self.upstream_tasks.add(depends_on)
        depends_on.downstream_tasks.add(self)

    def reset_task_dependencies(self):
        self.upstream_tasks.clear()
        self.downstream_tasks.clear()

    def get_all_filenames(self):
        """Identify the set of all filenames that pertain to this task
        """
        # TODO: when we allow for non-filesystem targets, this will
        # have to change to accomodate
        all_filenames = [self.creates]
        if isinstance(self.depends, (list, tuple)):
            all_filenames.extend(self.depends)
        elif self.depends is not None:
            all_filenames.append(self.depends)
        return all_filenames

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
        # probably a better way to get the protocol in python, but
        # this is fast and easy
        parts = element.split(':', 1)
        if len(parts) == 2:
            protocol = parts[0]
        else:
            protocol = "filesystem"

        method = getattr(self, "get_%s_state" % protocol, None)
        if method is None:
            raise NotImplementedError(
                "protocol '%s' is not implemented yet. Add it to the list here: "
                "https://github.com/deanmalmgren/data-workflow/issues/15"
            )
        return method(element)

    def get_filesystem_state(self, element):
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

    def get_config_state(self, element):
        state = None

        # write the data for this task to a stream so that we can use
        # the machinery in self.get_stream_state to calculate the
        # state
        msg = self.creates + str(self.depends) + str(self._command) + \
              str(self.alias)
        keys = self.command_attrs.keys()
        keys.sort()
        for k in keys:
            msg += k + str(self.command_attrs[k])
        return self.get_stream_state(StringIO.StringIO(msg))

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
            in_sync = False

        # if the data about this task is out of sync, then this task
        # must be executed
        in_sync = self.state_in_sync("config:"+self.id) and in_sync

        # otherwise, its in sync
        return in_sync

    def run(self, command):
        """Run the specified shell command using Fabric-like behavior"""
        return shell.run(self.root_directory, command)

    def clean_command(self):
        return "rm -rf %s" % self.creates

    def clean(self):
        """Remove the specified target"""
        self.run(self.clean_command())
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

    def command_message(self, command=None, color=colors.bold_white,
                        pre="|-> "):
        command = command or self.command
        if isinstance(command, (list, tuple)):
            msg = []
            for subcommand in command:
                msg.append(self.command_message(command=subcommand, 
                                                color=color, pre=pre))
            return '\n'.join(msg)
        msg = pre + command
        if color:
            msg = color(msg)
        return msg

    def __repr__(self):
        return '\n'.join([
            self.creates_message(),
            self.command_message()
        ])

class TaskGraph(object):
    """Simple graph implementation of a list of task nodes"""

    # relative location of various storage locations
    state_path = os.path.join(".workflow", "state.csv")
    duration_path = os.path.join(".workflow", "duration.csv")
    archive_dir = os.path.join(".workflow", "archive")

    def __init__(self, config_path):
        self.task_list = []
        self.task_dict = {}

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

    def _iter_helper(self, tasks, popmethod, updownstream):
        horizon = collections.deque(tasks)
        done, horizon_set = set(), set(tasks)
        task_order = []
        popmethod = getattr(horizon, popmethod)
        while horizon:
            task = popmethod()
            horizon_set.discard(task)
            done.add(task)
            task_order.append(task)
            updownset = getattr(task, updownstream)
            for task in updownset.difference(done):
                if task not in horizon_set:
                    horizon.append(task)
        return task_order

    def iter_bfs(self, tasks=None):
        """Breadth-first search of task dependencies, starting from the tasks
        that do not depend on anything.
        http://en.wikipedia.org/wiki/Breadth-first_search
        """
        # implement this starting from sources and working our way
        # downstream to make sure it is easy to specify particular tasks
        # on the command line (which should only re-run dependencies
        # as necessary)
        return self._iter_helper(
            tasks or self.get_source_tasks(),
            "popleft",
            "downstream_tasks",
        )

    def iter_dfs(self, tasks=None):
        """Depth-first search of task dependencies, starting from the tasks
        that do not have anything depending on them.
        http://en.wikipedia.org/wiki/Depth-first_search
        """
        # implement this starting from sinks and working our way
        # upstream to make sure it is easy to specify particular tasks
        # on the command line (which should only re-run dependencies
        # as necessary)
        return reversed(self._iter_helper(
            tasks or self.get_sink_tasks(),
            "pop",
            "upstream_tasks",
        ))

    def get_source_tasks(self):
        """Get the set of tasks that do not depend on anything else.
        """
        sink_tasks = set()
        for task in self.task_list:
            if not task.upstream_tasks:
                sink_tasks.add(task)
        return sink_tasks

    def get_sink_tasks(self):
        """Get the set of tasks that do not have any dependencies.
        """
        sink_tasks = set()
        for task in self.task_list:
            if not task.downstream_tasks:
                sink_tasks.add(task)
        return sink_tasks

    def add(self, task):
        """Connect the task to this TaskGraph instance. This stores the task
        in the TaskGraph.task_list and puts it in the
        TaskGraph.task_dict, keyed by task.creates and task.alias (if
        it exists).
        """
        task.graph = self
        self.task_list.append(task)
        if task.alias is not None:
            if self.task_dict.has_key(task.alias):
                raise NonUniqueTask("task `alias` '%s' is not unique"%task.alias)
            self.task_dict[task.alias] = task
        if self.task_dict.has_key(task.creates):
            raise NonUniqueTask("task `creates` '%s' is not unique"%task.creates)
        self.task_dict[task.creates] = task

    def subgraph_needed_for(self, task_ids):
        """Find the subgraph of all dependencies to run these tasks"""
        if not task_ids:
            return self

        # cast strings to task objects
        tasks = [self.task_dict[task_id] for task_id in task_ids]

        # add these tasks to the subgraph by iterating depth-first
        # search upstream
        subgraph = TaskGraph(self.config_path)
        for task in self.iter_dfs(tasks):
            subgraph.add(task)

        # reset the task connections to prevent the workflow from
        # going past the specified `creates` targets on the command
        # line
        for task in subgraph.task_list:
            task.reset_task_dependencies()
        subgraph.link_dependencies()
        subgraph.load_state()
        return subgraph

    def _link_dependency_helper(self, task, dependency):
        if dependency is not None:
            dependent_task = self.task_dict.get(dependency, None)

            # if dependent_task is None, make sure it exists on the
            # filesystem otherwise this Task is not properly defined
            if dependent_task is None:
                filename = os.path.join(self.root_directory, dependency)
                if not os.path.exists(filename):
                    raise InvalidTaskDefinition(
                        "Unknown `depends` declaration '%s'" % dependency
                    )
                return
            
            # now add the task dependency
            task.add_task_dependency(dependent_task)

    def link_dependencies(self):
        """Iterate over all tasks and make connections between tasks based on
        their dependencies.
        """
        for task in self.task_list:
            if isinstance(task.depends, (list, tuple)):
                for dependency in task.depends:
                    self._link_dependency_helper(task, dependency)
            else:
                self._link_dependency_helper(task, task.depends)

    def duration_string(self, duration):
        if duration < 10 * 60: # 10 minutes
            return "%.2f" % (duration) + " s" 
        elif duration < 2 * 60 * 60: # 2 hours
            return "%.2f" % (duration / 60) + " m"
        elif duration < 2 * 60 * 60 * 24: # 2 days
            return "%.2f" % (duration / 60 / 60) + " h"
        else:
            return "%.2f" % (duration / 60 / 60 / 24) + " d"

    def clean(self, export=False):
        """Run clean on every task and remove the state cache file
        """
        for task in self.task_list:
            if export:
                print(task.clean_command())
            else:
                task.clean()
        if os.path.exists(self.abs_state_path):
            if export:
                print("rm -f %s" % self.abs_state_path)
            else:
                os.remove(self.abs_state_path)

    def duration_message(self, tasks=None, color=colors.blue):
        tasks = tasks or self.task_list
        min_duration = 0.0
        for task in tasks:
            min_duration += self.task_durations.get(task.id, 0.0)
        max_duration, n_unknown, n_tasks = 0.0, 0, 0
        for task in self.iter_bfs(tasks):
            n_tasks += 1
            try:
                max_duration += self.task_durations[task.id]
            except KeyError:
                n_unknown += 1
        msg = ''
        if n_unknown>0:
            msg += "%d new tasks with unknown durations.\n" % (
                n_unknown, 
            )
        msg += "The remaining %d-%d tasks need to be executed,\n" % (
            len(tasks),
            n_tasks,
        )
        msg += "which will take between %s and %s." % (
            self.duration_string(min_duration),
            self.duration_string(max_duration),
        )
        if color:
            msg = color(msg)
        return msg

    @property
    def abs_state_path(self):
        """Convenience property for accessing state storage location"""
        return os.path.join(self.root_directory, self.state_path)

    @property
    def abs_duration_path(self):
        """Convenience property for accessing duration storage location"""
        return os.path.join(self.root_directory, self.duration_path)

    @property
    def abs_archive_dir(self):
        """Convenience property for accessing the archive location"""
        return os.path.join(self.root_directory, self.archive_dir)

    def read_from_storage(self, dictionary, storage_location):
        if os.path.exists(storage_location):
            with open(storage_location) as stream:
                reader = csv.reader(stream)
                for row in reader:
                    dictionary[row[0]] = row[1]

    def write_to_storage(self, dictionary, storage_location):
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
        self.read_from_storage(self.before_element_states, self.abs_state_path)
        self.read_from_storage(self.task_durations, self.abs_duration_path)

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
        dummy_task = Task(creates="dummy", command="dummy")
        dummy_task.graph = self
        for element, state in self.after_element_states.iteritems():
            if state is None:
                state = dummy_task.get_element_state(element)
                if state is None:
                    raise ElementNotFound(element)
                self.after_element_states[element] = state

        self.write_to_storage(self.after_element_states, self.abs_state_path)
        self.write_to_storage(self.task_durations, self.abs_duration_path)

    def write_archive(self):
        """Method to backup the current workflow
        """
        
        # for now, create archives based on the date. 
        # 
        # TODO: it would probably be better to specify by hg/git hash
        # id but this will do for now
        now = datetime.datetime.now()
        if not os.path.exists(self.abs_archive_dir):
            os.makedirs(self.abs_archive_dir)
        archive_name = os.path.join(
            self.abs_archive_dir,
            "%s.tar.bz2" % now.strftime("%Y%m%d%H%M%S"),
        )

        # get the set of all filenames that should be archived based
        # on the current workflow specification
        all_filenames = set([
            os.path.basename(self.config_path),
            self.state_path,
            self.duration_path,
        ])
        for task in self.task_list:
            all_filenames.update(task.get_all_filenames())

        # create the archive
        command = "tar cjf %s %s" % (archive_name, ' '.join(all_filenames))
        print(colors.bold_white(command))
        sys.stdout.flush()
        shell.run(self.root_directory, command)

        # TODO: what happens if equivalent archive already exists?

    def restore_archive(self):
        """Method to restore a previous archived workflow
        """

        # for now, restore the last archive in our archive directory. 
        #
        # TODO: it would probably be better to interact with the user
        # to determine which archive should be used
        available_archives = glob.glob(os.path.join(self.abs_archive_dir, '*'))
        available_archives.sort()
        archive_name = available_archives[-1]
        command = "tar xjf %s" % archive_name
        print(colors.bold_white(command))
        sys.stdout.flush()
        shell.run(self.root_directory, command)
