flo
===

``flo`` is a data workflow utility that is specifically designed to
enable rapid iteration and development of complex data pipelines. Its
:ref:`command line interface <command-line-interface>` and :ref:`task
configuration <flo.yaml-specification>` have many features that make
``flo`` ideal for developing data workflows, among them:

*  ``flo`` hashes the state of each file that it monitors to make it
   amenible to working with how most distributed version control
   systems work.
*  ``flo`` times each step of the analysis, :ref:`making it easy to
   determine how long any particular run will take <status>` before
   ``flo`` does anything.
*  ``flo`` comes with :ref:`command line autocompletion builtin
   <command-line-interface>`, making it easy to evaluate your options
   quickly in the terminal.
*  ``flo``\'s :ref:`task configuration is written in YAML
   <flo.yaml-specification>`, making it easy to read and write without
   having to know an :ref:`archaic language <GNU-make>` (sorry
   ``make``, its not you, its me).
*  ``flo`` is written in python, which is a native language to most
   data-savvy users to make it as easy as possible to maintain by the
   community.

..
   Here's a quick screencast of ``flo`` in action:

   .. todo:: make screencast!

If you're sold, :ref:`get started <quick-start>`. If not, read on:

.. toctree::
   op_ed
   quick_start
   yaml_specification
   command_line_interface
   developing
   changelog
   :maxdepth: 1

.. COMMENTING THIS OUT FOR NOW

   Indices and tables
   ==================

   * :ref:`genindex`
   * :ref:`modindex`
   * :ref:`search`

