"""Every subcommand within the workflow must have two public function,
an `add_to_parser` function that sets up the appropriate subcommand
parser with `argparse` and a `command` function that actually executes
that command.
"""

import argparse

from . import run, clean, archive
SUBCOMMANDS = [run, clean, archive]

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

def get_cli_parser():
    """Public function for creating a parser to execute all of the commands
    in this sub-package.
    """
    parser = argparse.ArgumentParser(
        description="Execute data workflows defined in workflow.yaml files",
    )
    subparsers = parser.add_subparsers(
        title='SUBCOMMANDS',
        description='valid subcommands',
        help='additional help'
    )
    for subcommand in SUBCOMMANDS:
        subcommand.add_to_parser(subparsers)
    return parser


