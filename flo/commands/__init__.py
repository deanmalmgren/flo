"""Every flo subcommand must have a Command class that inherits
from base.BaseCommand.
"""
import sys
import os
import argparse
import glob
from importlib import import_module

from ..exceptions import CommandLineException
from .base import BaseCommand
from . import run, clean, archive, status
from .. import colors

# NOTE: as of commit 54297065861b95922f1d26b892a63da33052a138, we
# imported these modules dynamically but this is rather slow for
# autocompletion
COMMAND_MODULES = [run, clean, archive, status]


def get_command_line_parser():
    """Public function for creating a parser to execute all of the commands
    in this sub-package.
    """
    command_line_parser = argparse.ArgumentParser(
        description="Execute data workflows defined in flo.yaml files",
    )
    subcommand_creator = command_line_parser.add_subparsers(
        title='SUBCOMMANDS',
    )
    for command_module in COMMAND_MODULES:
        command = command_module.Command(subcommand_creator)

        # this sets a default value for the command "option" so
        # that, when this Command is selected by argparse from the
        # command line, we know which comman instance it
        # corresponds with. See run_subcommand function below.
        command.option_parser.set_defaults(command=command)
    return command_line_parser


def run_subcommand(args):
    """This function runs the command that is selected by this particular
    subcommand parser.
    """
    try:
        command = args.__dict__.pop("command")
        command.execute(**args.__dict__)
    except (CommandLineException, KeyError) as error:
        print(colors.red(error))
        sys.exit(getattr(error, 'exit_code', 1))
