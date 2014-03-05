import sys
import os
import time
import csv
import StringIO
import collections
import datetime
import glob

import jinja2

from .exceptions import InvalidTaskDefinition, ResourceNotFound, NonUniqueTask
from . import colors
from . import shell
from . import resources

class Task(resources.base.BaseResource):

    def __init__(self, graph, creates=None, depends=None, alias=None, 
                 command=None, **kwargs):
        self.graph = graph
        self.creates = creates
        self.depends = depends
        self.command = command
        self.alias = alias

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

        # remember other attributes of this Task for rendering
        # purposes below
        self.command_attrs = kwargs
        self.command_attrs.update({
            'creates': self.creates,
            'depends': self.depends,
            'alias': self.alias,
        })

        # add this task to the task graph
        self.graph.add(self)

        # convert the creates/depends into resources
        self.depends_resources = resources.get_or_create(self.graph, self.depends)
        self.creates_resources = resources.get_or_create(self.graph, self.creates)

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

        # call the BaseResource.__init__ to get this to behave like an
        # resource here, too
        super(Task, self).__init__(self.graph, 'config:'+self.id)

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
        #
        # XXXX TODO: use the resources to get at this...
        all_filenames = [self.creates]
        if isinstance(self.depends, (list, tuple)):
            all_filenames.extend(self.depends)
        elif self.depends is not None:
            all_filenames.append(self.depends)
        return all_filenames

    @property
    def current_state(self):
        """Get the state of this task"""
        # write the data for this task to a stream so that we can use
        # the machinery in self._get_stream_state to calculate the
        # state
        msg = self.creates + str(self.depends) + str(self._command) + \
              str(self.alias)
        keys = self.command_attrs.keys()
        keys.sort()
        for k in keys:
            msg += k + str(self.command_attrs[k])
        return self._get_stream_state(StringIO.StringIO(msg))

    def in_sync(self):
        """Test whether this task is in sync with the stored state and
        needs to be executed
        """
        in_sync = self.state_in_sync()

        # if the creates doesn't exist, its not in sync and the task
        # must be executed
        if not os.path.exists(os.path.join(self.root_directory, self.creates)):
            in_sync = False

        # if any of the dependencies are out of sync, then this task
        # must be executed
        for resource in self.depends_resources:
            in_sync = in_sync and resource.state_in_sync()

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

        # Store the resources in a dictionary, keyed by name where the
        # values are resource instances
        self.resource_dict = {}

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

    def get_state_from_storage(self, resource):
        if os.path.exists(self.abs_state_path):
            with open(self.abs_state_path) as stream:
                reader = csv.reader(stream)
                for row in reader:
                    if row[0]==resource:
                        return row[1]

    def load_state(self):
        """Load the states of all resources (files, databases, etc). If the
        state file hasn't been stored yet, nothing happens. This also
        loads the duration statistics on this task.
        """
        self.read_from_storage(self.task_durations, self.abs_duration_path)

        # typecast the task_durations
        for task_id, duration in self.task_durations.iteritems():
            self.task_durations[task_id] = float(duration)

    def save_state(self):
        """Save the states of all resources (files, databases, etc). If the
        state file hasn't been stored yet, it creates a new one.
        """

        # store all of the resource states in a dictionary to save it
        # to csv
        after_resource_states = {}
        for name, resource in self.resource_dict.iteritems():
            after_resource_states[name] = resource.current_state

        self.write_to_storage(after_resource_states, self.abs_state_path)
        self.write_to_storage(self.task_durations, self.abs_duration_path)

    def write_archive(self):
        """Method to backup the current workflow
        """
        
        # for now, create archives based on the date. 
        # 
        # TODO: would it be better to specify by hg/git hash id? Doing
        # dates for now to make it easy to identify a good default
        # archive to restore in self.restore_archive (the last one)
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

    def restore_archive(self, archive):
        """Method to restore a previous archived workflow specified in
        `archive`. The archive path should be relative to the root of
        the project.
        """
        archive_name = os.path.join(self.root_directory, archive)
        command = "tar xjf %s" % archive_name
        print(colors.bold_white(command))
        sys.stdout.flush()
        shell.run(self.root_directory, command)

    def get_available_archives(self):
        """Method to list all of the available archives"""
        available_archives = self.get_abs_available_archives()
        return [os.path.relpath(a, self.root_directory) 
                for a in available_archives]

    def get_abs_available_archives(self):
        """Method to list all of the available archives"""
        available_archives = glob.glob(os.path.join(self.abs_archive_dir, '*'))
        available_archives.sort()
        return available_archives
