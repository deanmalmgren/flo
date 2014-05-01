import os
import sys

from ..exceptions import ShellError, CommandLineException
from ..notify import notify
from .base import BaseCommand, TaskIdMixin


class Command(BaseCommand, TaskIdMixin):
    help_text = "Run the task workflow."

    def manipulate_task_graph(self, task_id, start_at, skip, only):

        # --only is a synonym for setting start_at and task_id to be
        # the same thing. enforce logic here as it is not possible (?)
        # to do so with argparse directly
        # http://stackoverflow.com/q/14985474/564709
        if only is not None:
            if start_at is not None or task_id is not None:
                self.option_parser.error((
                    "--only can not be used with --start-at or specifying a "
                    "TASK_ID"
                ))
            else:
                start_at = task_id = only

        # restrict task graph as necessary for the purposes of running
        # the workflow
        if task_id is not None or start_at is not None:
            self.task_graph = self.task_graph.subgraph_needed_for(start_at,
                                                                  task_id)

        # if we are skipping a task, remove it from the task graph to
        # take it out of execution flow and avoid updating its status
        # in .flo/state.csv
        if skip:
            self.task_graph.remove_node_substituting_dependencies(skip)

    def inner_execute(self, task_id, start_at, skip, only, force,
                      mock_run=False):
        self.manipulate_task_graph(task_id, start_at, skip, only)

        # when the workflow is --force'd, this runs all
        # tasks. Otherwise, only runs tasks that are out of sync.
        if force:
            self.task_graph.run_all(mock_run=mock_run)
        else:
            self.task_graph.run_all_out_of_sync(mock_run=mock_run)

        # mark the self.task_graph as completing successfully to send the
        # correct email message
        self.task_graph.successful = True

    def execute(self, task_id=None, start_at=None, skip=None, only=None,
                force=False, notify_emails=None, **kwargs):
        super(Command, self).execute(**kwargs)
        try:
            self.inner_execute(task_id, start_at, skip, only, force)
        except CommandLineException, e:
            raise
        finally:
            if notify_emails:
                notify(*notify_emails)

    def add_common_run_options(self):
        # these options are used by both the `run` and `status` command
        self.option_parser.add_argument(
            '-f', '--force',
            action="store_true",
            help="Rerun entire workflow, regardless of task state.",
        )
        self.add_task_id_option('Specify a particular task to run.')
        self.option_parser.add_argument(
            '--start-at',
            type=str,
            metavar='TASK_ID',
            choices=self.available_task_ids,
            help=(
                'Specify a task to start from (run everything downstream, '
                'ignore everything upstream).'
            ),
        )
        self.option_parser.add_argument(
            '--skip',
            type=str,
            metavar='TASK_ID',
            choices=self.available_task_ids,
            help='Skip the specified task and ignore whether it is in sync.',
        )
        self.option_parser.add_argument(
            '--only',
            type=str,
            metavar='TASK_ID',
            choices=self.available_task_ids,
            help='Only run the specified task.',
        )

    def add_command_line_options(self):
        super(Command, self).add_command_line_options()
        self.add_common_run_options()
        self.option_parser.add_argument(
            '--notify',
            type=str,
            metavar='EMAIL',
            dest="notify_emails",
            nargs=1,
            help='Specify an email address to notify on completion.',
        )
