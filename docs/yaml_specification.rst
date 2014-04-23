flo.yaml specification
~~~~~~~~~~~~~~~~~~~~~~

Individual analysis tasks are defined as `YAML
objects <http://en.wikipedia.org/wiki/YAML#Associative_arrays>`__ in
``flo.yaml`` with something like this:

.. code:: yaml

    ---
    creates: path/to/some/output/file.txt
    depends: path/to/some/script.py
    command: python {{depends}} > {{creates}}

Every task YAML object must have a ```creates`` <#creates>`__ key and
can optionally contain ```command`` <#command>`__ and
```depends`` <#depends>`__ keys. The order of these keys does not
matter; the above order is chosen for explanatory purposes only.

creates
'''''''

The ``creates`` key defines the resource that is created. By default, it
is interpreted as a path to a file (relative paths are interpreted as
relative to the ``flo.yaml`` file). You can also specify a protocol,
such as ``mysql:database/table`` (see yet-to-be-implemented #15), for
non-file based resources.

depends
'''''''

The ``depends`` key defines the resource(s) on which this task depends.
It is common for ``depends`` to specify many things, including data
analysis scripts or other tasks from within the ``flo.yaml``. Multiple
dependencies can be defined in a `YAML
list <http://en.wikipedia.org/wiki/YAML#Lists>`__ like this:

.. code:: yaml

    depends:
      - path/to/some/script.py
      - another/task/creates/target.txt

command
'''''''

The ``command`` key defines the command(s) that should be executed to
produce the resource specified by the ``creates`` key. Like the
``depends`` key, multiple steps can be defined in a `YAML
list <http://en.wikipedia.org/wiki/YAML#Lists>`__ like this:

.. code:: yaml

    command:
      - mkdir -p $(dirname {{creates}})
      - python {{depends}} > {{creates}}

If the ``command`` key is omitted, this task is treated like a
pseudotask to make it easy to group together a collection of other tasks
like this:

.. code:: yaml

    creates: figures         # name of pseudotask
    depends:
      - path/to/figure/a.png # refers to another task in flo.yaml
      - path/to/figure/b.png # refers to another task in flo.yaml
      - path/to/figure/c.png # refers to another task in flo.yaml

templating variables
''''''''''''''''''''

Importantly, the ``command`` is rendered as a `jinja
template <http://jinja.pocoo.org/>`__ to avoid duplication of
information that is already defined in that task. Its quite common to
use ``{{depends}}`` and ``{{creates}}`` in the ``command``
specification, but you can also use other variables like this:

.. code:: yaml

    ---
    creates: path/to/some/output/file.txt
    sigma: 2.137
    depends: path/to/some/script.py
    command: python {{depends}} {{sigma} > {{creates}}

In the aforementioned example, ``sigma`` is only available when
rendering the jinja template for that task. If you'd like to use
``sigma`` in several other tasks, you can alternatively put it in a
global namespace in a flo.yaml like this (`similar example here <>`__):

.. code:: yaml

    ---
    sigma: 2.137
    tasks: 
      - 
        creates: path/to/some/output/file.txt
        depends: path/to/some/script.py
        command: python {{depends}} {{sigma} > {{creates}}
      -
        creates: path/to/another/output/file.txt
        depends:
          - path/to/another/script.py
          - path/to/some/output/file.txt
        command: python {{depends[0]}} {{sigma}} < {{depends[1]}} > {{creates}}

Another common use case for global variables is when you have several
tasks that all depend on the same file. You can also use jinja
templating in the ``creates`` and ``depends`` attributes of your
``flo.yaml`` like this:

.. code:: yaml

    ---
    input: data/sp500.html
    tasks:
      -
        creates: "{{input}}"
        command:
          - mkdir -p $(dirname {{creates}})
          - wget http://en.wikipedia.org/wiki/List_of_S%26P_500_companies -O {{creates}}
      -
        creates: data/names.dat
        depends:
          - src/extract_names.py
          - "{{input}}"
        command: python {{depends|join(' ')}} > {{creates}}
      -
        creates: data/symbols.dat
        depends:
          - src/extract_symbols.py
          - "{{input}}"
        command: python {{depends|join(' ')}} > {{creates}}

There are several `examples <examples/>`__ for more inspiration on how
you could use the flo.yaml specification. If you have suggestions for
other ideas, please `add them <issues>`__!
