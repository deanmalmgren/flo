import os
import time
import six
from six import StringIO
import copy

from ..exceptions import InvalidTaskDefinition, CommandLineException
from .. import colors
from .. import shell
from .. import resources
from .. import templates
from ..types import UniqueOrderedList

if six.PY2:
    str_types = (str, unicode)
else:
    str_types = str


def _cast_as_list(obj):
    if isinstance(obj, (list, tuple)):
        return obj
    elif obj is None:
        return []
    elif isinstance(obj, str_types):
        return [obj]
    else:
        raise TypeError("unexpected type passed to _cast_as_list")


class Task(resources.base.BaseResource):

    def __init__(self, graph, creates=None, depends=None,
                 command=None, **kwargs):
        self.graph = graph
        self._creates = creates
        self._depends = depends
        self._command = command
        self._kwargs = copy.deepcopy(kwargs)

        # quick type checking to make sure the tasks in the
        # configuration file are valid
        if self._creates is None:
            raise InvalidTaskDefinition(
                "every task must define a `creates`",
                self.yaml_data,
            )
        if not isinstance(self._creates, str_types):
            raise InvalidTaskDefinition(
                "each task must define a single `creates` as a string",
                self.yaml_data,
            )
        if self._command is None:
            raise InvalidTaskDefinition(
                "every task must define a `command`",
                self.yaml_data,
            )

        # remember other attributes of this Task for rendering
        # purposes below
        self.attrs = kwargs

        # render the creates and depends templates as necessary. this
        # is to address issue #33
        # https://github.com/deanmalmgren/flo/issues/33
        self.creates = self.render_template(self._creates)
        self.depends = self.render_template(self._depends)

        # update the attrs to reflect any changes from the template
        # rendering from global variables
        self.attrs.update({
            'creates': self.creates,
            'depends': self.depends,
        })

        # save the original command strings in _command for checking
        # the state of this command and render the jinja template for
        # the command
        self.command = self.render_command_template()

        # add this task to the task graph
        self.graph.add(self)

        # this is used to store resources that are associated with
        # this task. These data structures are managed within
        # BaseResource
        self.depends_resources = []
        self.creates_resources = []
        resources.add_to_task(self)

        # create some data structures for storing the set of tasks on
        # which this task depends (upstream_tasks) on what depends on
        # it (downstream_tasks).
        self.downstream_tasks = set()
        self.upstream_tasks = set()

        # call the BaseResource.__init__ to get this to behave like an
        # resource here, too
        super(Task, self).__init__(self.graph, self.config_resource_id)

    @property
    def creates_list(self):
        return _cast_as_list(self.creates)

    @property
    def depends_list(self):
        return _cast_as_list(self.depends)

    @property
    def command_list(self):
        return _cast_as_list(self.command)

    @property
    def yaml_data(self):
        out = copy.deepcopy(self._kwargs)
        out.update({
            "creates": self._creates,
            "depends": self._depends,
            "command": self._command,
        })
        return out

    @property
    def id(self):
        """Canonical way to identify this Task"""
        return self.creates

    @property
    def config_resource_id(self):
        """Canonical way to identify the resource id associated with this Task
        """
        return 'config:' + self.id

    @property
    def root_directory(self):
        """Easy access to the graph's root_directory, which is stored once for
        every task
        """
        return self.graph.root_directory

    def iter_resources(self):
        for resource in self.creates_resources:
            yield resource
        for resource in self.depends_resources:
            yield resource

    def add_task_dependency(self, depends_on):
        self.upstream_tasks.add(depends_on)
        depends_on.downstream_tasks.add(self)

    def substitute_dependencies(self):
        """Substitute this task's dependencies into its upstream and
        downstream tasks. This is useful when a Task is being removed
        from the TaskGraph but its dependencies should be preserved
        for the remaining tasks in the TaskGraph.
        """
        for downstream_task in self.downstream_tasks:
            downstream_task.upstream_tasks.remove(self)
            downstream_task.upstream_tasks.update(self.upstream_tasks)
        for upstream_task in self.upstream_tasks:
            upstream_task.downstream_tasks.remove(self)
            upstream_task.downstream_tasks.update(self.downstream_tasks)

    def disconnect_resources(self):
        """Disconnect this task from all resources. This is useful when a Task
        is being removed from the TaskGraph and we do not want the
        Task's sync status affected.
        """
        for resource in self.depends_resources:
            resource.depends_tasks.remove(self)
            if len(resource.depends_tasks) == 0:
                resource.delete()
        for resource in self.creates_resources:
            if resource.creates_task == self:
                resource.delete()
        self.graph.resource_dict.pop(self.config_resource_id)

    def reset_task_dependencies(self):
        self.upstream_tasks.clear()
        self.downstream_tasks.clear()

    def get_all_filenames(self):
        """Identify the set of all filenames that pertain to this task
        """
        # TODO: when we allow for non-filesystem targets, this will
        # have to change to accomodate
        all_filenames = set()
        for resource in self.iter_resources():
            all_filenames.add(resource.get_filename())
        return all_filenames

    def get_current_state(self):
        """Get the state of this task"""
        # write the data for this task to a stream so that we can use
        # the machinery in self.get_stream_state to calculate the
        # state
        msg = self.creates + str(self.depends) + str(self._command)
        keys = sorted(self.attrs.keys())
        for k in keys:
            msg += k + str(self.attrs[k])
        return self.get_stream_state(StringIO(msg))

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
        return shell.run(self.root_directory, command)

    def clean_command(self):
        return "rm -rf %s" % self.creates

    def clean(self):
        """Remove the specified target"""
        self.run(self.clean_command())
        self.graph.logger.info("removed %s" % self.creates_message())

    def mock_run(self):
        """Mock run this task by displaying output as if it were run"""
        self.graph.logger.info(str(self))

    def timed_run(self):
        """Run the specified task from the root of the workflow"""

        # useful message about starting this task and what it is
        # called so users know how to re-call this task if they
        # notice something fishy during execution.
        self.graph.logger.info(self.creates_message())
        start_time = time.time()

        # confirm that all depends resources exist on the filesystem
        if not all(resource.exists() for resource in self.depends_resources):
            unmet = self.depends
            if isinstance(unmet, list):
                unmet = '{} and {} do'.format(', '.join(unmet[:-1]),
                                              unmet[-1])
            else:
                unmet = unmet + ' does'
            raise CommandLineException(unmet + (
                " not exist just before running this task. "
                "Double check the `depends` to confirm that these "
                "dependencies are correct for this task."
            ))

        # run each command for this task
        for command in self.command_list:
            self.graph.logger.info(self.command_message(command))
            self.run(command)

        # confirm that the creates resources exists on the filesystem
        if not all(resource.exists() for resource in self.creates_resources):
            raise CommandLineException(self.creates + (
                " does not exist after running the previous commands. "
                "Double check the syntax to confirm that these commands "
                "will actually create it."
            ))

        # stop the clock and alert the user to the clock time spent
        # running the task
        self.duration = time.time() - start_time
        self.graph.logger.info(self.duration_message())

        # store the duration on the graph object
        self.graph.task_durations[self.id] = self.duration

    def render_template(self, template):
        """Render a `template` using self.attrs as a template context.
        """

        if template is None:
            return None

        # if template is a list, make sure to render each element of
        # the list
        if isinstance(template, (list, tuple)):
            return [templates.render_from_string(t, **self.attrs)
                    for t in template]
        else:
            return templates.render_from_string(template, **self.attrs)

    def render_command_template(self):
        """Uses jinja template syntax to render the command from the other
        data specified in the YAML file
        """
        return self.render_template(self._command)

    def duration_message(self, color=colors.blue):
        msg = "%79s" % self.graph.duration_string(self.duration)
        if color:
            msg = color(msg)
        return msg

    def creates_message(self, color=colors.green):
        msg = self.creates
        if color:
            msg = color(msg)
        return msg

    def command_message(self, command, color=colors.bold_white,
                        pre="|-> "):
        msg = pre + command
        if color:
            msg = color(msg)
        return msg

    def __repr__(self):
        return '\n'.join(
            [self.creates_message()] +
            [self.command_message(command=command)
             for command in self.command_list]
        )
