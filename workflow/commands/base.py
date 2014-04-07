from ..parser import load_task_graph
from ..exceptions import ConfigurationNotFound


class BaseCommand(object):
    help_text = ''

    def __init__(self, subcommand_creator):

        try:
            self.task_graph = load_task_graph()
        except ConfigurationNotFound:
            self.task_graph = None

        # set up the subcommand options
        self.subcommand_creator = subcommand_creator
        self.option_parser = self.subcommand_creator.add_parser(
            self.get_command_name(),
            help=self.help_text,
            description=self.help_text,
        )
        self.add_command_line_options()

    def get_command_name(self):
        """The command name defaults to the name of the module."""
        return self.__module__.rsplit('.', 1)[1]

    def add_command_line_options(options):
        pass

    def execute(self, *args, **kwargs):
        raise NotImplementedError("must be overwritten by base classes")


class TaskIdMixin(object):
    def add_task_id_option(self, help_text):
        """This method streamlines the addition of adding a task_id option to
        the command line parser.
        """
        available_tasks = []
        if self.task_graph:
            available_tasks = self.task_graph.get_task_ids()
        self.option_parser.add_argument(
            'task_id',
            metavar='TASK_ID',
            type=str,
            choices=available_tasks,
            nargs='?',  # '*', this isn't working for some reason
            help=help_text,
        )
