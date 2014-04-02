import os
import sys

from ..exceptions import ShellError
from ..notify import notify
from .base import BaseCommand, TaskIdMixin


class Command(BaseCommand, TaskIdMixin):
    help_text = "Run the task workflow."

    def inner_execute(self, task_id, force, dry_run):

        # REFACTOR TODO: this is a temporary hack
        task_graph = self.task_graph

        # REFACTOR TODO: this function is almost certainly overcommented
        # and should be broken into separate methods in a TaskGraph

        # if any tasks are specified, limit the task graph to only those
        # tasks that are required to create the specified tasks
        if task_id is not None:
            task_graph = task_graph.subgraph_needed_for([task_id])

        # iterate through every task in the task graph and find the set of
        # tasks that have to be executed. we do this first so we can alert
        # the user as to how long this workflow will take. breadth first
        # search on entire task graph to make sure the out_of_sync_tasks
        # are created in the appropriate order for subsequent steps.
        out_of_sync_tasks = []
        for task in task_graph.iter_bfs():

            # regardless of whether we force the execution of the command,
            # run the in_sync method, which calculates the state of the
            # task and all `creates` / `depends` elements
            if not task.is_pseudotask() and (force or not task.in_sync()):
                out_of_sync_tasks.append(task)

        # report the minimum amount of time this will take to execute and
        # execute all tasks
        if out_of_sync_tasks:
            task_graph.logger.info(
                task_graph.duration_message(out_of_sync_tasks)
            )
            for task in task_graph.iter_bfs(out_of_sync_tasks):
                # We unfortunately need (?) to re-run in_sync here in case
                # things change during the course of a run. This is not
                # ideal but makes it possible to estimate the duration of
                # a workflow run, which is pretty valuable
                if not task.is_pseudotask() and (force or not task.in_sync()):
                    if not dry_run:
                        try:
                            task.timed_run()
                        except (KeyboardInterrupt, ShellError), e:
                            # on keyboard interrupt or error on executing
                            # a specific step, make sure all previously
                            # run tasks have their state properly stored
                            # and make sure re-running the workflow will
                            # rerun the task that was underway. we do this
                            # by saving the state of everything but
                            # overridding the state of the creates
                            # resource for this task before exiting
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
