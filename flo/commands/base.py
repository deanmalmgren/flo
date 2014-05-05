from ..parser import load_task_graph, get_task_kwargs_list
from ..exceptions import ConfigurationNotFound


class BaseCommand(object):
    help_text = ''

    def __init__(self, subcommand_creator):

        # keep a local copy of the config file which is useful during
        # autocompletion
        self.config = None

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

    def add_command_line_options(self):
        self.option_parser.add_argument(
            '-c', '--config',
            type=str,
            help='Specify a particular YAML configuration file.',
        )

    def execute(self, config=None):
        self.config = config
        self.task_graph = load_task_graph(config)

    # this is a performance optimization to make it possible to use
    # the flo.yaml file to inform useful *and responsive* tab
    # completion on the command line _task_kwargs_list is used as a
    # local cache that is loaded once and inherited by all subclasses.
    @property
    def task_kwargs_list(self):
        try:
            return get_task_kwargs_list(config=self.config)
        except ConfigurationNotFound:
            return []

    @property
    def available_task_ids(self):
        task_ids = []
        for task_kwargs in self.task_kwargs_list:
            task_id = task_kwargs.get('alias') or task_kwargs.get('creates')
            task_ids.append(task_id)
        task_ids.sort()
        return task_ids

    def task_ids_completer(self, prefix, parsed_args, **kwargs):
        # this custom completer makes autocompletion work properly
        # when an alternative configuration file has been specified
        # https://argcomplete.readthedocs.org/en/latest/#specifying-completers
        self.config = parsed_args.config
        return [task_id for task_id in self.available_task_ids
                if task_id.startswith(prefix)]

    def add_task_id_option(self, help_text):
        """This method streamlines the addition of adding a task_id option to
        the command line parser.
        """
        # this uses a customized completer to correctly detect the
        # configuration file during completion, which isn't possible
        # by parsing sys.argv (which is what argparse natively does). 
        help_text += " Tab complete to view options."
        self.option_parser.add_argument(
            'task_id',
            metavar='TASK_ID',
            type=str,
            choices=self.available_task_ids,
            nargs='?',
            help=help_text,
        ).completer = self.task_ids_completer
        # TODO: using `nargs='*'` does not work with `choices`
        # specified for some reason. For now, electing to use
        # `choices` and nargs='?'` so that command line autocomplete
        # works. Also tried to use `nargs=argcomplete.REMAINDER` and
        # `action='append'` but neither of these options worked either.
