import jinja2

from . import exceptions

class Task(object):

    def __init__(self, creates=None, depends=None, alias=None, command=None, 
                 **kwargs):
        self.creates = creates
        self.depends = depends
        self.command = command
        self.alias = alias

        # remember other attributes of this Task for rendering
        # purposes below
        self.command_attrs = kwargs
        self.command_attrs.update({
            'creates': self.creates,
            'depends': self.depends,
            'alias': self.alias,
        })

        # quick type checking to make sure the tasks in the
        # configuration file are valid
        if self.creates is None:
            raise exceptions.InvalidTaskDefinition(
                "every task must define a `creates`"
            )
        if self.command is None:
            raise exceptions.InvalidTaskDefinition(
                "every task must define a `command`"
            )

        # render the jinja template for the command
        self.command = self.render_command_template()
        print self.command

    def in_sync(self):
        """test whether this task is in sync with the stored state and
        needs to be executed
        """
        return False

    def execute(self):
        """run the specified task"""
        return None

    def render_command_template(self, command=None):
        """Uses jinja template syntax to render the command from the other
        data specified in the YAML file
        """

        # if command is a list, render recursively
        command = command or self.command
        if isinstance(command, (list, tuple)):
            return [self.render_command_template(cmd) for cmd in command]

        # otherwise, need to render the template with Jinja2
        env = jinja2.Environment()
        template = env.from_string(command)
        return template.render(self.command_attrs)

class TaskGraph(object):
    """Simple graph implementation of a list of task nodes"""

    def __init__(self):
        self.tasks = []

    def add(self, task):
        self.tasks.append(task)

    def __iter__(self):
        return iter(self.tasks)
