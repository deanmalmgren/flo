import sys
import os
import time
import csv
import StringIO
import collections
import datetime
import glob
from distutils.util import strtobool

import jinja2

from .exceptions import InvalidTaskDefinition, ResourceNotFound, NonUniqueTask
from . import colors
from . import shell
from . import resources
from . import logger

class Task(resources.base.BaseResource):

    def __init__(self, graph, creates=None, depends=None, alias=None, 
                 command=None, **kwargs):
        self.graph = graph
        self._creates = creates
        self._depends = depends
        self._command = command
        self._alias = alias

        # quick type checking to make sure the tasks in the
        # configuration file are valid
        if self._creates is None:
            raise InvalidTaskDefinition(
                "every task must define a `creates`"
            )

        # remember other attributes of this Task for rendering
        # purposes below
        self.attrs = kwargs

        # render the creates and depends templates as necessary. this
        # is to address issue #33
        # https://github.com/deanmalmgren/data-workflow/issues/33
        self.creates = self.render_template(self._creates)
        self.depends = self.render_template(self._depends)
        self.alias = self.render_template(self._alias)

        # update the attrs to reflect any changes from the template
        # rendering from global variables
        self.attrs.update({
            'creates': self.creates,
            'depends': self.depends,
            'alias': self.alias,
        })

        # save the original command strings in _command for checking
        # the state of this command and render the jinja template for
        # the command
        self.command = self.render_command_template()

        # add this task to the task graph
        self.graph.add(self)

        # this is used to store resources that are associated with
        # this task. This is set up in TaskGraph.link_dependencies
        self.depends_resources = []
        self.creates_resources = []

        # create some data structures for storing the set of tasks on
        # which this task depends (upstream_tasks) on what depends on
        # it (downstream_tasks)
        self.downstream_tasks = set()
        self.upstream_tasks = set()        

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
        every task
        """
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
        if self.is_pseudotask():
            all_filenames = []
        if isinstance(self.depends, (list, tuple)):
            all_filenames.extend(self.depends)
        elif self.depends is not None:
            all_filenames.append(self.depends)
        return all_filenames

    def get_current_state(self):
        """Get the state of this task"""
        # write the data for this task to a stream so that we can use
        # the machinery in self.get_stream_state to calculate the
        # state
        msg = self.creates + str(self.depends) + str(self._command) + \
              str(self.alias)
        keys = self.attrs.keys()
        keys.sort()
        for k in keys:
            msg += k + str(self.attrs[k])
        return self.get_stream_state(StringIO.StringIO(msg))

    def is_pseudotask(self):
        """Check to see if this task is a pseudotask.
        """
        return self._command is None

    def in_sync(self):
        """Test whether this task is in sync with the stored state and
        needs to be executed
        """

        # if the creates doesn't exist, its not in sync and the task
        # must be executed
        if not os.path.exists(os.path.join(self.root_directory, self.creates)):
            return False

        # if this task or any of its dependencies are out of sync,
        # then this task must be executed. We use `all` here to
        # deliberately stop checking states when any resource state is
        # out of sync (this is more computationally efficient for
        # checking large file hashes)
        return self.state_in_sync() and all(
            resource.state_in_sync() for resource in self.depends_resources
        )

    def run(self, command):
        """Run the specified shell command using Fabric-like behavior"""
        if command is not None:
            return shell.run(self.root_directory, command)

    def clean_command(self):
        return "rm -rf %s" % self.creates

    def clean(self):
        """Remove the specified target"""
        if not self.is_pseudotask():
            self.run(self.clean_command())
            self.graph.logger.info("removed %s" % self.creates_message())

    def timed_run(self, command=None):
        """Run the specified task from the root of the workflow"""

        # REFACTOR TODO: separate out the running of a the command
        # from the timing of the command

        # start of task execution
        start_time = None
        if command is None:

            # useful message about starting this task and what it is
            # called so users know how to re-call this task if they
            # notice something fishy during execution.
            self.graph.logger.info(self.creates_message())

            # start a timer so we can keep track of how long this task
            # executes. Its important that we're timing watch time, not
            # CPU time
            start_time = time.time()

        # execute a sequence of commands by recursively calling this
        # method
        #
        # REFACTOR TODO: either (i) make _execute_helper method OR force
        # self.command to ALWAYS be a list
        command = command or self.command
        if isinstance(command, (list, tuple)):
            for cmd in command:
                self.timed_run(cmd)

        # if its not a list or a tuple, then this string should be
        # executed. Update the user on our progress so far, be sure to
        # change to the root directory of the workflow, and execute
        # the command. This takes inspiration from how
        # fabric.operations.local works http://bit.ly/1dQEgjl
        else:
            self.graph.logger.info(self.command_message(command=command))
            self.run(command)

        # stop the clock and alert the user to the clock time spent
        # running the task
        if start_time:
            self.duration = time.time() - start_time
            self.graph.logger.info(self.duration_message())

            # store the duration on the graph object
            self.graph.task_durations[self.id] = self.duration

    def render_template(self, template):
        """Render a `template` using self.attrs as a template
        context. `template` can either be a list or a string."""

        if template is None:
            return None

        # if template is a list, make sure to render each element of
        # the list
        if isinstance(template, (list, tuple)):
            return [self.render_template(ts) for ts in template]

        # render the template as if its a jinja template
        env = jinja2.Environment()
        template_obj = env.from_string(template)
        return template_obj.render(self.attrs)

    def render_command_template(self):
        """Uses jinja template syntax to render the command from the other
        data specified in the YAML file
        """
        if self.is_pseudotask():
            return None
        return self.render_template(self._command)

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
        if command is None:
            return '' # no command message for pseudotasks
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
    internals_path = ".workflow"
    state_path = os.path.join(internals_path, "state.csv")
    duration_path = os.path.join(internals_path, "duration.csv")
    log_path = os.path.join(internals_path, "workflow.log")
    archive_dir = os.path.join(internals_path, "archive")

    def __init__(self, config_path):
        self.task_list = []
        self.task_dict = {}

        # store paths once for all tasks and make sure the base
        # directory exists
        self.config_path = config_path
        self.root_directory = os.path.dirname(config_path)
        directory = os.path.dirname(self.abs_state_path)
        if not os.path.exists(directory):
            os.makedirs(directory)
        if not os.path.exists(self.abs_archive_dir):
            os.makedirs(self.abs_archive_dir)

        # Store the resources in a dictionary, keyed by name where the
        # values are resource instances
        self.resource_dict = {}

        # store the time that this task takes
        self.task_durations = {}

        # instantiate the logger instance for this workflow
        self.logger = logger.configure(self)

        # the success status is used for managing notification emails
        # in an intelligent way
        self.successful = False

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
                    horizon_set.add(task)
        return task_order

    def iter_bfs(self, tasks=None):
        """Breadth-first search of task dependencies, starting from the tasks
        that do not depend on anything.
        http://en.wikipedia.org/wiki/Breadth-first_search
        """
        # REFACTOR TODO: if iter_dfs is NOT needed, we can make this __iter__
        # to make things easier to understand.

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
        # REFACTOR TODO: is depth-first search needed here?!?!
        subgraph = TaskGraph(self.config_path)
        for task in self.iter_dfs(tasks):
            subgraph.add(task)

        # reset the task connections to prevent the workflow from
        # going past the specified `creates` targets on the command
        # line 
        #
        # REFACTOR TODO: this is damaging self --- this particular TaskGraph
        # instance. this can definitely be cleaned up somehow. make a
        # copy of Task objects? Another approach: have self manipulate
        # the tasks in this TaskGraph?
        for task in subgraph.task_list:
            task.reset_task_dependencies()
        subgraph.dereference_depends_aliases()
        subgraph.link_dependencies()
        subgraph.load_state()
        return subgraph

    def _dereference_alias_helper(self, name):
        if name is None:
            return 
        for task in self.task_list:
            if task.alias == name:
                return task.creates

    def dereference_depends_aliases(self):
        """This converts every alias used in a depends statement into the
        corresponding `creates` element in that task declaration. 
        """
        for task in self.task_list:
            if isinstance(task.depends, (list, tuple)):
                for i, d in enumerate(task.depends):
                    dd = self._dereference_alias_helper(d)
                    if dd is not None:
                        task.depends[i] = dd
            else:
                dd = self._dereference_alias_helper(task.depends)
                if dd is not None:
                    task.depends = dd

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

            # instantiate the resources associated with this task here
            # to make sure we can resolve aliases if they exist.
            task.depends_resources = resources.get_or_create(
                self, task.depends
            )
            task.creates_resources = resources.get_or_create(
                self, task.creates
            )
            
            # omit creates resources from pseudotasks. this is
            # getting sloppy. should probably do this within a task?
            if task.is_pseudotask():
                task.creates_resources = []
                del self.resource_dict[task.creates]

            # link up the dependencies
            if isinstance(task.depends, (list, tuple)):
                for dependency in task.depends:
                    self._link_dependency_helper(task, dependency)
            else:
                self._link_dependency_helper(task, task.depends)

    def confirm_clean(self, task_list=None, include_internals=False, pause=0.5):
        self.logger.info(colors.red(
            "Please confirm that you want to delete the following files:"
        ))
        time.sleep(pause)
        task_list = task_list or self.task_list
        if include_internals:
            self.logger.info(green(self.internals_path))
        for task in task_list:
            if not task.is_pseudotask():
                self.logger.info(task.creates_message())
        yesno = raw_input(colors.red("Delete aforementioned files? [Y/n] "))
        if yesno == '':
            yesno = 'y'
        return strtobool(yesno)

    def clean(self, task_list=None, include_internals=False):
        """Remove appropriate internal files managed by workflow as well as
        any resulting files created by the specified `task_list`.
        """
        if os.path.exists(self.abs_state_path) and task_list is None:
            os.remove(self.abs_state_path)
        if include_internals:
            shell.run(self.root_directory, "rm -rf %s" % self.internals_path)
            self.logger.info(
                "removed %s" % colors.green(self.internals_path)
            )
        task_list = task_list or self.task_list
        for task in task_list:
            task.clean()

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
        tasks = tasks or self.task_list
        min_duration = 0.0
        for task in tasks:
            min_duration += self.task_durations.get(task.id, 0.0)
        max_duration, n_unknown, n_tasks = 0.0, 0, 0
        for task in self.iter_bfs(tasks):
            if not task.is_pseudotask():
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
        if max_duration == min_duration == 0.0:
            msg += "which will take an indeterminate amount of time."
        elif max_duration == min_duration:
            msg += "which will take approximately %s." % (
                self.duration_string(min_duration),
            )
        else:
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
    def abs_log_path(self):
        """Convenience property for accessing log storage location"""
        return os.path.join(self.root_directory, self.log_path)

    @property
    def abs_archive_dir(self):
        """Convenience property for accessing the archive location"""
        return os.path.join(self.root_directory, self.archive_dir)

    def read_from_storage(self, storage_location):
        dictionary = {}
        if os.path.exists(storage_location):
            with open(storage_location) as stream:
                reader = csv.reader(stream)
                for row in reader:
                    dictionary[row[0]] = row[1]
        return dictionary

    def write_to_storage(self, dictionary, storage_location):
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
        self.task_durations.update(
            self.read_from_storage(self.abs_duration_path)
        )

        # typecast the task_durations
        for task_id, duration in self.task_durations.iteritems():
            self.task_durations[task_id] = float(duration)

    def save_state(self, override_resource_states=None):
        """Save the states of all resources (files, databases, etc). If the
        state file hasn't been stored yet, it creates a new one. Can
        optionally pass override_resource_states to set the states of
        particular elements, which can be useful for handling keyboard
        interrupts, for example.
        """

        # read all of the old storage states first, then over write
        # the old states with the current states before writing to a
        # CSV. this is important for situations where a subgraph is
        # selected to run
        after_resource_states = self.read_from_storage(self.abs_state_path)
        for name, resource in self.resource_dict.iteritems():
            after_resource_states[name] = resource.get_current_state()

        # if override states are provided, update the resources
        # accordingly
        if isinstance(override_resource_states, dict):
            after_resource_states.update(override_resource_states)

        self.write_to_storage(after_resource_states, self.abs_state_path)
        self.write_to_storage(self.task_durations, self.abs_duration_path)

    def write_archive(self, exclude_internals=False):
        """Method to backup the current workflow
        """
        
        # for now, create archives based on the date. 
        # 
        # TODO: would it be better to specify by hg/git hash id? Doing
        # dates for now to make it easy to identify a good default
        # archive to restore in self.restore_archive (the last one)
        now = datetime.datetime.now()
        archive_name = os.path.join(
            self.abs_archive_dir,
            "%s.tar.bz2" % now.strftime("%Y%m%d%H%M%S"),
        )

        # get the set of all filenames that should be archived based
        # on the current workflow specification
        all_filenames = set([os.path.basename(self.config_path)])
        if not exclude_internals:
            all_filenames.update(set([
                self.state_path,
                self.duration_path,
                self.log_path,
            ]))
        for task in self.task_list:
            all_filenames.update(task.get_all_filenames())

        # create the archive. filenames are ordered here so that the
        # corresponding archive will have a consistent md5 hash (which is
        # used in functional tests).
        command = "tar cjf %s %s" % (
            archive_name, 
            ' '.join(sorted(all_filenames)),
        )
        self.logger.info(colors.bold_white(command))
        shell.run(self.root_directory, command)

    def restore_archive(self, archive):
        """Method to restore a previous archived workflow specified in
        `archive`. The archive path should be relative to the root of
        the project.
        """
        archive_name = os.path.join(self.root_directory, archive)
        command = "tar xjf %s" % archive_name
        self.logger.info(colors.bold_white(command))
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
