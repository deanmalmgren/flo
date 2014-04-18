from ..parser import load_task_graph, get_task_kwargs_list
from ..exceptions import ConfigurationNotFound


class BaseCommand(object):
    help_text = ''

    def __init__(self, subcommand_creator):

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

    def _init_task_graph(self):
        self.task_graph = load_task_graph()

    def execute(self, *args, **kwargs):
        self._init_task_graph()


class TaskKwargsListMixin(object):
    """Any Command that uses flo.yaml to influence available command
    line options should inherit from this class so that we only read and
    parse the flo.yaml file *once*.
    """

    # this is a performance optimization to make it possible to use
    # the flo.yaml file to inform useful *and responsive* tab
    # completion on the command line _task_kwargs_list is used as a
    # local cache that is loaded once and inherited by all subclasses.
    @property
    def task_kwargs_list(self):
        try:
            return get_task_kwargs_list()
        except ConfigurationNotFound:
            return []


class TaskIdMixin(TaskKwargsListMixin):

    @property
    def available_task_ids(self):
        task_ids = []
        for task_kwargs in self.task_kwargs_list:
            task_id = task_kwargs.get('alias') or task_kwargs.get('creates')
            task_ids.append(task_id)
        task_ids.sort()
        return task_ids

    def add_task_id_option(self, help_text):
        """This method streamlines the addition of adding a task_id option to
        the command line parser.
        """
        help_text += " Tab complete to view options."
        self.option_parser.add_argument(
            'task_id',
            metavar='TASK_ID',
            type=str,
            choices=self.available_task_ids,
            nargs='?',
            help=help_text,
        )
        # TODO: using `nargs='*'` does not work with `choices`
        # specified for some reason. For now, electing to use
        # `choices` and nargs='?'` so that command line autocomplete
        # works. Also tried to use `nargs=argcomplete.REMAINDER` and
        # `action='append'` but neither of these options worked either.
