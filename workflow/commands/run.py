import os
import sys

from ..exceptions import ShellError, CommandLineException
from ..notify import notify
from .base import BaseCommand, TaskIdMixin


class Command(BaseCommand, TaskIdMixin):
    help_text = "Run the task workflow."

    def inner_execute(self, task_id, force, dry_run):

        # REFACTOR TODO: this function is almost certainly overcommented
        # and should be broken into separate methods in TaskGraph

        if task_id is not None:
            self.task_graph = self.task_graph.subgraph_needed_for([task_id])

        # we do this first so we can alert the user as to how long
        # this workflow will take. 
        if force:
            out_of_sync_tasks = list(task_graph.iter_graph())
        else:
            out_of_sync_tasks = task_graph.get_out_of_sync_tasks()

        # REFACTOR TODO: maybe separate out timing better? separate
        # out exceptions into different function? figure out how to
        # deal with force better so that iter_graph can really give us
        # just what we want... OR have two methods -- one that
        # executes EVERYTHING no matter what and another that checks
        # to see if a task is in sync before it runs.

        if out_of_sync_tasks:
            task_graph.logger.info(
                task_graph.duration_message(out_of_sync_tasks)
            )
            for task in task_graph.iter_graph(out_of_sync_tasks):
                # We unfortunately need (?) to re-run in_sync here in case
                # things change during the course of a run. This is not
                # ideal but makes it possible to estimate the duration of
                # a workflow run, which is pretty valuable
                if not task.is_pseudotask() and (force or not task.in_sync()):
                    if not dry_run:
                        try:
                            task.timed_run()
                        except (KeyboardInterrupt, ShellError), e:
                            task_graph.save_state(
                                override_resource_states={task.name: ''},
                            )
                            sys.exit(getattr(e, 'exit_code', 1))
                    elif dry_run:
                        task_graph.logger.info(str(task))

        # if no tasks needed to be executed, then alert the user.
        else:
            task_graph.logger.info(
                "No tasks are out of sync in the workflow defined in '%s'" % (
                    os.path.relpath(task_graph.config_path, os.getcwd())
                )
            )

        # otherwise, we need to recalculate hashes for everything that is
        # out of sync
        if not dry_run:
            task_graph.save_state()

        # mark the task_graph as completing successfully to send the
        # correct email message
        task_graph.successful = True

    def execute(self, task_id=None, force=False, dry_run=False,
                notify_emails=None):
        try:
            self.inner_execute(task_id, force, dry_run)
        except CommandLineException, e:
            print(e)
            sys.exit(getattr(e, 'exit_code', 1))
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
        self.add_task_id_option('Specify a particular task to run.')
