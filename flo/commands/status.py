from .run import Command as RunCommand


class Command(RunCommand):
    help_text = (
        "Check the status of the current workflow "
        "to see which tasks, if any, are out of sync and would be run."
    )

    def inner_execute(self, task_id, start_at, skip, only, force):
        self.manipulate_task_graph(task_id, start_at, skip, only)

        # when the workflow is --force'd, this runs all
        # tasks. Otherwise, only runs tasks that are out of sync.
        if force:
            self.task_graph.run_all(mock_run=True)
        else:
            self.task_graph.run_all_out_of_sync(mock_run=True)

        # mark the self.task_graph as completing successfully to send the
        # correct email message
        self.task_graph.successful = True

    def add_command_line_options(self):
        self.add_common_run_options()
