"""Every subcommand within the workflow must have two public functions,
an `add_to_parser` function that sets up the appropriate subcommand
parser with `argparse` and a `command` function that actually executes
that command.
"""

import argparse

from ..exceptions import CommandLineException
from . import run, clean, archive
SUBCOMMAND_MODULES = [
    run,
    clean,
    archive
]


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
        command = module.Command(subcommand_creator)
    return command_line_parser


def run_subcommand(args):
    """This function runs the command that is selected by this particular
    subcommand parser.
    """
    command = args.__dict__.pop("command")
    command.execute(**args.__dict__)
