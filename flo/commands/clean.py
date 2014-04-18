from .base import BaseCommand, TaskIdMixin


class Command(BaseCommand, TaskIdMixin):
    help_text = (
        "Remove all `creates` targets defined in workflow. If a `task_id` is "
        "specified, only remove that target."
    )

    def execute(self, task_id=None, force=False, include_internals=False):
        super(Command, self).execute()
        kwargs = {
            'include_internals': include_internals,
        }

        # if a task_id is specified, only remove this particular
        # task. otherwise, remove everything.
        if task_id is not None:
            kwargs['task_list'] = [self.task_graph.task_dict[task_id]]

        # print a warning message before removing all tasks. Briefly
        # pause to make sure user sees the message at the top.
        if force or self.task_graph.get_user_clean_confirmation(**kwargs):
            self.task_graph.clean(**kwargs)

    def add_command_line_options(self):
        self.option_parser.add_argument(
            '-f', '--force',
            action="store_true",
            help="Remove all `creates` targets without confirmation.",
        )
        self.option_parser.add_argument(
            '--include-internals',
            action="store_true",
            help="Remove all files in the .flo/ directory.",
        )
        self.add_task_id_option(
            'Specify a particular task to clean rather than all of them.'
        )
