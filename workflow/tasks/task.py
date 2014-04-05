import os
import time
import StringIO
import copy

import jinja2

from ..exceptions import InvalidTaskDefinition
from .. import colors
from .. import shell
from .. import resources


class Task(resources.base.BaseResource):

    def __init__(self, graph, creates=None, depends=None, alias=None,
                 command=None, **kwargs):
        self.graph = graph
        self._creates = creates
        self._depends = depends
        self._command = command
        self._alias = alias
        self._kwargs = copy.deepcopy(kwargs)

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
        # this task. This is set up in TaskGraph._link_dependencies
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
    def yaml_data(self):
        out = copy.deepcopy(self._kwargs)
        out.update({
            "creates": self._creates,
            "depends": self._depends,
            "command": self._command,
            "alias": self._alias,
        })
        return out

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
            return ''  # no command message for pseudotasks
        msg = pre + command
        if color:
            msg = color(msg)
        return msg

    def __repr__(self):
        return '\n'.join([
            self.creates_message(),
            self.command_message()
        ])
