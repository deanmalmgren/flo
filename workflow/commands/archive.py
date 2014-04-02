from .base import BaseCommand


class Command(BaseCommand):
    help_text="Create and restore backup archives of data analysis workflows."

    def execute(self, restore=False, exclude_internals=False):
        if restore:
            self.task_graph.restore_archive(restore)
        else:
            self.task_graph.write_archive(exclude_internals=exclude_internals)

    def add_command_line_options(self):

        # get the available archives if the task_graph was found
        available_archives = []
        if self.task_graph is not None:
            available_archives = self.task_graph.get_available_archives()

        self.option_parser.add_argument(
            '--restore',
            choices=available_archives,
            default=False,
            nargs='?',
            help="Restore the state of the workflow."
        )
        self.option_parser.add_argument(
            '--exclude-internals',
            action="store_true",
            help="exclude internals in the .workflow/ directory from archive",
        )
