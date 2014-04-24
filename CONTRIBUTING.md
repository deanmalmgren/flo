Any and all contributions are welcome and appreciated. To make it easy
to keep things organized, this project uses the
[general guidelines](https://help.github.com/articles/using-pull-requests)
for the fork-branch-pull request model for github.

### Reporting bugs

If you observe an unexpected behavior, tasks being re-run when they
shouldn't be, suspicious output, etc, one of the simplest ways of
reporting the bug is to [create a gist](https://gist.github.com/) with
the relevant `flo.yaml` and any relevant source code that is necessary
for reproducing the issue. Another possibility is to execute `flo
archive` to create a tarball with the offending code and share a
dropbox link or put it in a gist as well.

### Contributing to the source code

As a general rule of thumb, the goal of this package is to be as
readable as possible to make it easy for novices and experts alike to
contribute to the source code in meaningful ways. Pull requests that
favor cleverness or optimization over readability are less likely to
be incorporated into the source code.

To make this notion of "readability" more concrete, here are a few
stylistic guidelines that were implemented:

* write functions and methods that can
  [fit on a screen or two of a standard terminal](https://www.kernel.org/doc/Documentation/CodingStyle)
  --- no more than approximately 40 lines.

* unless it makes code less readable, adhere to
  [PEP 8](http://legacy.python.org/dev/peps/pep-0008/) style
  recommendations --- use an appropriate amount of whitespace.

* [code comments should be about *what* is being done, not *how* it is being done](https://www.kernel.org/doc/Documentation/CodingStyle)
  --- that should be self-evident from the code itself.

### A few words on code organization

Many of the modules in the `flo` python package have pretty
self-evident roles (*e.g.*, `flo.colors` provides convenience
functions for color output). Some things though, 

**bin/flo** This is the main script that is run on the command
line. It calls routines from `flo.commands`.

**flo.commands** The modules and functions in this sub-package
provide high-level functionality of what flo actually does. Each
module has a `Command` class that inherits from
`flo.commands.base.BaseCommand` which specifies how that command
should be run.

**flo.parser** This module is the sole location that reads `flo.yaml`
configuration and instantiates `TaskGraph` instances.

**flo.tasks** This module contains most of the nuts and bolts of
`Task` definitions and `TaskGraph` dependencies

**flo.resources** Resources are things like files, directories,
databases, etc that should be monitored by `flo`. This subpackage
enables the functionality to check if resources are out of sync.
