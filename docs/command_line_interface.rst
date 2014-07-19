.. _command-line-interface:

command line interface
~~~~~~~~~~~~~~~~~~~~~~

This package ships with the ``flo`` command, which embodies the entire
command line interface for this package. This command can be run from
the directory that contains ``flo.yaml`` or any of its child
directories. Output has been formatted to be as useful as possible,
including the task names that are run, the commands that are run, and
how long each task takes. For convenience, this information is also
stored in ``.flo/flo.log``.

To make the command line interface as usable as possible,
autocompletion of available options with workflow is enabled by
@kislyuk's amazing `argcomplete
<https://github.com/kislyuk/argcomplete>`__ package.  Follow
instructions to `enable global autocomplete
<https://github.com/kislyuk/argcomplete#activating-global-completion>`__
and you should be all set. As an example, this is also configured in
the `virtual machine provisioning for this project
<http://github.com/deanmalmgren/flo/blob/master/provision/development.sh#L17>`__. Here,
we elaborate on a few key features of ``flo``; see ``flo --help`` for
details about all available functionality.

.. _flo-run:

running workflows
'''''''''''''''''

By default, the ``flo run`` command will execute the entire workflow, or
at least the portion of it that is "out of sync" since the last time it
ran. Executing ``flo run`` twice in a row without editing any files in
the interim will not rerun any steps. If you edit a particular file in
the workflow and re-execute ``flo run``, this will only re-execute the
parts that have been affected by the change. This makes it very easy to
iterate quickly on data analysis problems without having to worry about
re-running an arsenal commands --- you only have to remember one,
``flo run``.

.. code-block:: bash

    flo run                # runs everything for the first time
    flo run                # nothing changed; runs nothing
    edit path/to/some/script.py
    flo run                # only runs the parts that are affected by change

Importantly, if you edit a particular task in the ``flo.yaml`` itself,
this will cause that particular task to be re-run as well:

.. code-block:: bash

    flo run
    edit flo.yaml          # change a particular task's command
    flo run                # rerun's that command and any dependent task

The ``flo`` command is able to do this by tracking the status of all
``creates``, ``depends``, and task definitions by hashing the contents
of these resources. If the contents in any ``depends`` or the task
itself has changed since the last time that task was run, ``flo`` will
run that task. For reference, the hashes of all of the ``creates``,
``depends``, and workflow task definitions are in ``.flo/state.csv``.

.. _flo-config:

same project, different workflows
'''''''''''''''''''''''''''''''''

Naturally, there will be times when you'll want to have separate sets
of steps to accomplish different things. One simple way to separate
your workflow configuration is by putting them in two separate files,
say ``figures.yaml`` and ``analysis.yaml``. You can then specify
running these separate workflows on the command line with the
``--config`` option like this:

.. code-block:: bash

    flo run --config figures.yaml
    flo run --config analysis.yaml

All other behaviors of the YAML configuration and use of the ``flo``
command remain exactly the same.

limiting flo run execution
''''''''''''''''''''''''''

Oftentimes we do not want to run the entire workflow, but only a
particular component of it. Like GNU make, you can specify a particular
task by its ``creates`` value on the command line like this:

.. code-block:: bash

    flo run path/to/some/output/file.txt

This limits ``flo`` to only executing the task defined in
``path/to/some/output/file.txt`` and all of its recursive upstream
dependencies. Other times we do not want to run the entire workflow,
but run everything after a specific task. We can do that like this:

.. code-block:: bash

    flo run --start-at path/to/some/file.txt

This limits ``flo`` to only executing the task defined in
``path/to/some/file.txt`` and all of its recursive **downstream**
dependencies. This can be combined with ``flo run task_id`` to only all
tasks between two specified tasks like this:

.. code-block:: bash

    flo run --start-at path/to/some/file.txt path/to/some/output/file.txt

If you ever want to only run one task, say a task that creates
``path/to/some/file.txt``, you can specify that task as both the
starting and ending point of the workflow run with ``--only``:

.. code-block:: bash

    # these two things are the same
    flo run --only path/to/some/file.txt
    flo run --start-at path/to/some/file.txt path/to/some/file.txt

In some situations --- especially with very long-running tasks that
you know haven't been affected by changes --- it is convenient to be
able to skip particular tasks like this:

.. code-block:: bash

    flo run --skip path/to/some/file.txt

This eliminates the task associated with ``path/to/some/file.txt`` from
the workflow but preserves the dependency chain so that other tasks are
still executed in the proper order.

Sometimes it is convenient to rerun an entire workflow, regardless of
the current status of the files that were generated.

.. code-block:: bash

    flo run
    # don't do anything for several months
    echo "Rip Van Winkle awakens and wonders, where did I leave off again?"
    echo "Screw it, lets just redo the entire analysis"
    flo run --force

For long-running workflows, it is convenient to be alerted when the
entire workflow completes. The ``--notify`` command line option makes it
possible to have the last 100 lines of the ``.flo/flo.log`` sent to an
email address specified on the command line.

.. code-block:: bash

    flo run --notify j.doe@example.com

.. _status:

I'm nervous, what's going to happen?
''''''''''''''''''''''''''''''''''''

While :ref:`we don't recommend it <op-ed>`, its not uncommon to get
"in the zone" and make several edits to analysis scripts before
re-running your workflow. Because we're human, its easy to incorrectly
remember the files you edited and how they may affect re-running the
workflow. To help, the ``flo status`` command lets you see which
commands will be run and approximately how much time it should take
(!!!).

.. code-block:: bash

    flo run
    edit path/to/some/script.py
    edit path/to/another/script.py
    echo "a long time passes"
    flo status             # don't run anything, just report what would be done

For reference, ``flo`` stores the duration of each task in
``.flo/duration.csv``. Another way you can comfort yourself is by
looking at the status visualization.

.. code-block:: bash

    flo status --serve

which displays something like this:

.. figure:: http://i.imgur.com/uWNK9xO.png
    :alt: status visual

Starting over
'''''''''''''

Sometimes you want to start with a clean slate. Perhaps the data you
originally started with is dated or you want to be confident a workflow
properly runs from start to finish before inviting collaborators.
Whatever the case, the ``flo clean`` command can be useful for removing
all ``creates`` targets that are defined in ``flo.yaml``. With the
``--force`` command line option, you can remove all files without having
to confirm that you want to remove them. If you just want to remove a
particular target, you can use ``flo clean task_id`` to only remove that
``creates`` target.

.. code-block:: bash

    flo clean              # asks user if they want to remove `creates` results
    flo clean --force      # removes all `creates` targets without confirmation
    flo clean a/task       # only remove the a/task target

Saving results
''''''''''''''

Before removing or totally redoing an analysis, I've often found it
useful to backup my results and compare the differences later. The
``flo archive`` command makes it easy to quickly backup an entire flo
(including generated ``creates`` targets, source code specified in
``depends``, and the underlying ``flo.yaml``) and compare it to previous
versions.

.. code-block:: bash

    flo archive            # store archive in .flo/archives/*.tar.bz2
    for i in `seq 20`; do
        edit path/to/some/script.py
        flo run
    done
    echo 'oh crap, this sequence of changes was a mistake'
    flo archive --restore  # uncompresses archive
