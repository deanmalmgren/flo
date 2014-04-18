import os
import glob

from .base import BaseCommand
from ..parser import find_config_path
from ..tasks.graph import TaskGraph
from ..exceptions import ConfigurationNotFound


class Command(BaseCommand):
    help_text = "Create and restore backup archives of workflows."

    def execute(self, restore=False, exclude_internals=False):
        super(Command, self).execute()
        if restore:
            self.task_graph.restore_archive(restore)
        else:
            self.task_graph.write_archive(exclude_internals=exclude_internals)

    def get_available_archives(self):
        # this method extracts the available archives by understanding
        # where TaskGraph stores the information
        try:
            config_path = find_config_path()
        except ConfigurationNotFound:
            return []
        abs_project_root = os.path.dirname(config_path)
        abs_archive_dir = os.path.join(abs_project_root, TaskGraph.archive_dir)
        abs_archives = glob.glob(os.path.join(abs_archive_dir, "*"))
        return [os.path.relpath(a, abs_project_root) for a in abs_archives]

    def add_command_line_options(self):
        self.option_parser.add_argument(
            '--restore',
            metavar='ARCHIVE_PATH',
            choices=self.get_available_archives(),
            default=False,
            nargs='?',
            help=(
                "Restore the state of the workflow. "
                "Tab complete to view available archives."
            ),
        )
        self.option_parser.add_argument(
            '--exclude-internals',
            action="store_true",
            help="Exclude internals in the .flo/ directory from archive",
        )
