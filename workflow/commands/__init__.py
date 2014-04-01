"""Every subcommand within the workflow must have two public functions,
an `add_to_parser` function that sets up the appropriate subcommand
parser with `argparse` and a `command` function that actually executes
that command.
"""

import argparse

from ..exceptions import CommandLineException
from . import run, clean, archive
SUBCOMMAND_MODULES = [run, clean, archive]

# REFACTOR TODO: tried to clean this up a bit to make the actual
# `workflow` script easier to read. Do we want to have a Command class
# rather than an `add_to_parser` and `command` function in each
# submodule? This is the approach taken by Django and Scrapy, for
# example. Might not be that important, but it could be a good way to
# factor out common elements of commands If we used classes, then we
# could:
#   * provide a common interface for instantiating parsers
#   * use the doc string on the class as the default help text
#   * name the command based on the .py file it is in
#   * load a task graph consistently
#   * consistently mark things as successful


def get_command_line_parser():
    """Public function for creating a parser to execute all of the commands
    in this sub-package.
    """
    command_line_parser = argparse.ArgumentParser(
        description="Execute data workflows defined in workflow.yaml files",
    )
    subcommand_creator = command_line_parser.add_subparsers(
        title='SUBCOMMANDS',
    )
    for module in SUBCOMMAND_MODULES:
        module_name = module.__name__.rsplit('.', 1)[1]
        command_doc = module.command.__doc__
        options = subcommand_creator.add_parser(
            module_name, help=command_doc, description=command_doc,
        )
        options = module.add_command_line_options(options)

        # this sets up the function that should be run if this
        # subcommand is specified on the command line. See
        # run_subcommand for how this is used.
        options.set_defaults(command=module.command)
    return command_line_parser


def run_subcommand(args):
    # This is where the actual command is run. This is set up with
    # the get_command_line_parser above.
    command = args.__dict__.pop("command")
    command(**args.__dict__)
