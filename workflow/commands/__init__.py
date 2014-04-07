"""Every workflow subcommand must have a Command class that inherits
from base.BaseCommand.
"""
import os
import argparse
import pkgutil
from importlib import import_module

from ..exceptions import CommandLineException
from .base import BaseCommand


def _iter_command_cls():
    """Dynamically find all modules in this directory with a Command
    class that inherits from BaseCommand.
    """
    this_directory = os.path.dirname(os.path.abspath(__file__))
    for dummy, module_name, dummy in pkgutil.iter_modules([this_directory]):
        module = import_module("."+module_name, package=__package__)
        command_cls = getattr(module, "Command", None)
        if command_cls is not None and issubclass(command_cls, BaseCommand):
            yield command_cls


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
    for command_cls in _iter_command_cls():
        command = command_cls(subcommand_creator)

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
    command = args.__dict__.pop("command")
    command.execute(**args.__dict__)
