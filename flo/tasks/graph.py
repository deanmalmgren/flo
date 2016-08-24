import sys
import os
import time
import csv
import collections
import datetime
import glob
from distutils.util import strtobool
import json
import six
from six.moves import input

import networkx as nx

from ..exceptions import NonUniqueTask, ShellError, CommandLineException
from .. import colors
from .. import shell
from .. import resources
from .. import logger
from .task import Task


class TaskGraph(object):
    """Simple graph implementation of a list of task nodes"""

    # relative location of various storage locations
    internals_path = ".flo"
    state_path = os.path.join(internals_path, "state.csv")
    duration_path = os.path.join(internals_path, "duration.csv")
    log_path = os.path.join(internals_path, "flo.log")
    archive_dir = os.path.join(internals_path, "archive")

    def __init__(self, config_path, task_kwargs_list):
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

        # add tasks and load all dependencies between tasks
        for task_kwargs in task_kwargs_list:
            task = Task(self, **task_kwargs)
        self._link_dependencies()
        self._load_state()

        # confirm that this is a DAG without any dependency loops
        nx_graph = self.get_networkx_graph(task_id_only=True)
        if not nx.is_directed_acyclic_graph(nx_graph):
            msg = "This task graph has the following dependency cycles:\n\n"
            cycles = nx.simple_cycles(nx_graph)
            for cycle in cycles:
                msg += '  %s\n' % cycle[0]
                for task_id in cycle[1:]:
                    msg += '    -> %s\n' % task_id
            raise CommandLineException(msg)

    def iter_tasks(self, tasks=None):
        """Iterate over graph starting from `tasks` with a customized
        breadth-first search to ensure that task dependencies are
        preserved and that tasks are returned in a deterministic
        order. One important difference between this method and
        standard breadth first search is that we want to track the
        *maximum* distance from any source to every other task to make
        sure the ordering is correct.

        If no starting `tasks` are specified, this algorithm starts
        with the set of tasks that do not depend on anything.
        """
        source_tasks = tasks or self.get_source_tasks()
        distances = {}
        horizon = list(source_tasks)
        done, horizon_set = set(), set(source_tasks)
        source_tasks = set(source_tasks)
        while horizon:
            # before popping task off the horizon list, make sure all
            # of its dependencies have been completed
            found = False
            for task in horizon:
                if (
                    task in source_tasks or
                    not task.upstream_tasks.difference(done)
                ):
                    found = True
                    break
            if not found:
                raise Exception("NOT FOUND %s" % ([t.id for t in horizon], ))
            if task in source_tasks:
                distance = 0
            else:
                distance = max([distances.get(x)
                                for x in task.upstream_tasks]) + 1
            distances[task] = distance
            horizon.remove(task)
            horizon_set.discard(task)
            done.add(task)
            for downstream_task in task.downstream_tasks.difference(done):
                if downstream_task not in horizon_set:
                    horizon.append(downstream_task)
                    horizon_set.add(downstream_task)

        # now create a decorated list of based on the distance and
        # ordering in the YAML file
        decorated_list = []
        for task, distance in six.iteritems(distances):
            decorated_list.append((
                distance, self.task_list.index(task), task,
            ))
        decorated_list.sort()
        for distance, index, task in decorated_list:
            yield task

    def get_source_tasks(self):
        """Get the set of tasks that do not depend on anything else.
        """
        source_tasks = []
        for task in self.task_list:
            if not task.upstream_tasks:
                source_tasks.append(task)
        return source_tasks

    def get_sink_tasks(self):
        """Get the set of tasks that do not have any dependencies.
        """
        sink_tasks = []
        for task in self.task_list:
            if not task.downstream_tasks:
                sink_tasks.append(task)
        return sink_tasks

    def get_out_of_sync_tasks(self):
        out_of_sync_tasks = []
        for task in self.iter_tasks():
            if not task.in_sync():
                out_of_sync_tasks.append(task)
        return out_of_sync_tasks

    def add(self, task):
        """Connect the task to this TaskGraph instance. This stores the task
        in the TaskGraph.task_list and puts it in the
        TaskGraph.task_dict, keyed by task.creates.
        """
        self.task_list.append(task)
        if task.creates in self.task_dict:
            raise NonUniqueTask(
                "task `creates` '%s' is not unique" % task.creates
            )
        self.task_dict[task.creates] = task

    def remove_node_substituting_dependencies(self, task_id):
        """Remove the Task associated with task_id and substitute its
        downstream dependencies with task_id's dependencies
        """
        # remove this element from the TaskGraph
        task = self.task_dict.pop(task_id)
        self.task_list.remove(task)
        if task_id in self.task_durations:
            self.task_durations.pop(task_id)

        # remove this task's resources if they are not specified in
        # other tasks
        task.disconnect_resources()

        # substitute its dependencies so that its upstream and
        # downstream nodes in the task graph know the proper execution
        # order
        task.substitute_dependencies()

        # for good measure
        del task

    def subgraph_needed_for(self, start_at, end_at):
        """Find the subgraph of all dependencies to run these tasks. Returns a
        new graph.
        """
        assert start_at or end_at, "one of {start_at,end_at} must be a task id"
        start, end = [self.task_dict.get(start_at), self.task_dict.get(end_at)]
        if None in [start, end]:
            graph = self.get_networkx_graph()
            if start:
                task_subset = nx.descendants(graph, start)
                task_subset.add(start)
            elif end:
                task_subset = nx.ancestors(graph, end)
                task_subset.add(end)
        elif start == end:
            task_subset = set([start])
        else:
            graph = self.get_networkx_graph()
            task_subset = set()
            for path in nx.all_simple_paths(graph, start, end):
                task_subset.update(path)

        # make sure the tasks are added to the subgraph in the same
        # order as the original configuration file
        tasks_kwargs_list = [task.yaml_data for task in self.task_list
                             if task in task_subset]
        subgraph = TaskGraph(self.config_path, tasks_kwargs_list)
        return subgraph

    def get_networkx_graph(self, task_id_only=False):
        graph = nx.DiGraph()
        if task_id_only:
            graph.add_nodes_from([task.id for task in self.task_list])
            for node in self.task_list:
                for child in node.downstream_tasks:
                    graph.add_edge(node.id, child.id)
        else:
            graph.add_nodes_from(self.task_list)
            for node in graph:
                for child in node.downstream_tasks:
                    graph.add_edge(node, child)
        return graph

    def _dereference_alias_helper(self, name):
        if name is None:
            return None
        for task in self.task_list:
            if task.alias == name:
                return task.creates

    def _dereference_depends_aliases(self):
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

    def _link_dependencies(self):
        """Iterate over all tasks and make connections between tasks based on
        their dependencies.
        """
        for task in self.task_list:
            for resource in task.depends_resources:
                if isinstance(resource.creates_task, Task):
                    task.add_task_dependency(resource.creates_task)

    def get_user_clean_confirmation(self, task_list=None,
                                    include_internals=False):
        """This method gets user confirmation about cleaning up the workflow
        """
        self.logger.info(colors.red(
            "Please confirm that you want to delete the following files:"
        ))
        time.sleep(0.5)
        task_list = task_list or self.task_list
        if include_internals:
            self.logger.info(green(self.internals_path))
        for task in task_list:
            self.logger.info(task.creates_message())
        yesno = input(colors.red("Delete aforementioned files? [Y/n] "))
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

    def status_json(self):
        result = {"nodes": [], "links": []}
        node_index = {}
        for i, task in enumerate(self.iter_tasks()):
            node_index[task] = i
            result["nodes"].append({
                "task_id": task.id,
                "duration": self.task_durations.get(task.id, None),
                "in_sync": task.in_sync(),
            })
        for task in node_index:
            for child in task.downstream_tasks:
                result["links"].append({
                    "source": node_index[task],
                    "target": node_index[child],
                })
        return json.dumps(result)

    def duration_string(self, duration):
        if duration < 10 * 60:  # 10 minutes
            return "%.2f" % (duration) + " s"
        elif duration < 2 * 60 * 60:  # 2 hours
            return "%.2f" % (duration / 60) + " m"
        elif duration < 2 * 60 * 60 * 24:  # 2 days
            return "%.2f" % (duration / 60 / 60) + " h"
        else:
            return "%.2f" % (duration / 60 / 60 / 24) + " d"

    def duration_message(self, tasks, color=colors.blue):
        if tasks is None:
            tasks = list(self.iter_tasks())
        if len(tasks) == 0:
            return "No tasks are out of sync in this workflow (%s)" % (
                os.path.relpath(self.config_path, os.getcwd())
            )
        min_duration = 0.0
        for task in tasks:
            min_duration += self.task_durations.get(task.id, 0.0)
        max_duration, n_unknown, n_tasks = 0.0, 0, 0
        for task in self.iter_tasks(tasks):
            n_tasks += 1
            try:
                max_duration += self.task_durations[task.id]
            except KeyError:
                n_unknown += 1
        msg = ''
        if n_unknown > 0:
            msg += "There are %d new tasks with unknown durations.\n" % (
                n_unknown,
            )
        if len(tasks) == n_tasks:
            msg += "The remaining %d tasks need to be executed,\n" % n_tasks
        else:
            msg += "The remaining %d to %d tasks need to be executed,\n" % (
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

    def _run_helper(self, starting_tasks, do_run_func, mock_run):
        """This is a convenience method that is used to slightly modify the
        behavior of running a workflow depending on the circumstances.
        """
        self.logger.info(self.duration_message(starting_tasks))
        for task in self.iter_tasks(starting_tasks):
            if do_run_func(task):
                if mock_run:
                    task.mock_run()
                else:
                    try:
                        task.timed_run()
                    except (KeyboardInterrupt, ShellError) as error:
                        self.save_state(
                            override_resource_states={task.name: ''},
                        )
                        sys.exit(getattr(error, 'exit_code', 1))
        if not mock_run:
            self.save_state()

    def run_all(self, mock_run=False):
        """Execute all tasks in the workflow, regardless of whether they are
        in sync or not.
        """
        def do_run_func(task):
            return True
        self._run_helper(None, do_run_func, mock_run)

    def run_all_out_of_sync(self, mock_run=False):
        """Execute all tasks in the workflow that are out of sync at runtime.
        """
        def do_run_func(task):
            return not task.in_sync()
        self._run_helper(self.get_out_of_sync_tasks(), do_run_func, mock_run)

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
            for item in six.iteritems(dictionary):
                writer.writerow(item)

    def get_state_from_storage(self, resource):
        if os.path.exists(self.abs_state_path):
            with open(self.abs_state_path) as stream:
                reader = csv.reader(stream)
                for row in reader:
                    if row[0] == resource:
                        return row[1]

    def _load_state(self):
        """Load the states of all resources (files, databases, etc). If the
        state file hasn't been stored yet, nothing happens. This also
        loads the duration statistics on this task.
        """
        self.task_durations.update(
            self.read_from_storage(self.abs_duration_path)
        )

        # typecast the task_durations
        for task_id, duration in six.iteritems(self.task_durations):
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
        for name, resource in six.iteritems(self.resource_dict):
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
