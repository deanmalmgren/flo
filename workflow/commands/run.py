import os
import sys
import re

from ..exceptions import ShellError, CommandLineException
from ..notify import notify
from .base import BaseCommand, TaskIdMixin


class Command(BaseCommand, TaskIdMixin):
    help_text = "Run the task workflow."

    def inner_execute(self, task_id, force, dry_run, **regex_limitations):
        # restrict task graph as necessary for the purposes of running
        # the workflow
        if task_id is not None:
            self.task_graph = self.task_graph.subgraph_needed_for([task_id])

        # update the regex limitations on the graph if they are
        # specified on the command line
        self.task_graph.regex_limitations.update(regex_limitations)

        # when the workflow is --force'd, this runs all
        # tasks. Otherwise, only runs tasks that are out of sync.
        if force:
            self.task_graph.run_all(mock_run=dry_run)
        else:
            self.task_graph.run_all_out_of_sync(mock_run=dry_run)

        # mark the self.task_graph as completing successfully to send the
        # correct email message
        self.task_graph.successful = True

    def execute(self, task_id=None, force=False, dry_run=False,
                notify_emails=None, **kwargs):
        super(Command, self).execute()
        try:
            self.inner_execute(task_id, force, dry_run, **kwargs)
        except CommandLineException, e:
            raise
        finally:
            if notify_emails:
                notify(*notify_emails)

    def add_command_line_options(self):
        self.option_parser.add_argument(
            '-f', '--force',
            action="store_true",
            help="Rerun entire workflow, regardless of task state.",
        )
        # TODO: should this be broken out as a separate `status`
        # command? This would make workflow behave more like version
        # control. Pros and cons?
        self.option_parser.add_argument(
            '-d', '--dry-run',
            action="store_true",
            help=(
                "Do not run workflow, just report which tasks would be run "
                "and how long it would take."
            ),
        )
        self.option_parser.add_argument(
            '--notify',
            type=str,
            metavar='EMAIL',
            dest="notify_emails",
            nargs=1,
            help='Specify an email address to notify on completion.',
        )
        self.add_regex_options()
        self.add_task_id_option('Specify a particular task to run.')

    def add_regex_options(self):
        group = self.option_parser.add_argument_group(
            'Regular expression completion options'
        )
        for task_kwargs in self.task_kwargs_list:
            depends = task_kwargs.get('depends')
            if isinstance(depends, (str, unicode)):
                self.add_regex_options_helper(group, depends)
            elif isinstance(depends, (list, tuple)):
                for d in depends:
                    self.add_regex_options_helper(group, d)

    def add_regex_options_helper(self, group, resource):
        resource_regex = re.compile(resource)
        for regex_option in resource_regex.groupindex:
            group.add_argument(
                '--' + regex_option.replace('_', '-'),
                type=str,
                nargs="?",
                help='Specify particular regex match for <%s>' % regex_option,
            )
