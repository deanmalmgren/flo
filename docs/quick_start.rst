quick start
~~~~~~~~~~~

1. *Install this package.*

``bash    pip install -e git+https://github.com/deanmalmgren/flo#egg=flo``

2. *Write a flo.yaml.* Create a ``flo.yaml`` file in the root of your
   project. ``flo.yaml`` can `have many
   features <#floyaml-specification>`__, but the basic idea is to make
   it easy to quickly define a sequence of dependent tasks in an
   easy-to-read way. There are several `examples <examples/>`__, the
   simplest of which is the `hello-world
   example <examples/hello-world/flo.yaml>`__. Briefly, every task is a
   YAML object that has a ``creates`` key that represents the resource
   that is created by this task and a ``command`` key that defines the
   command that are required to create the resource defined in
   ``creates``. You can optionally define a ``depends`` key that lists
   resources, either filenames on disk or other task ``creates``
   targets, to quickly set up dependency chains. You can optionally omit
   the ``command`` key to create pseudotasks that are collections of
   other tasks for quickly running a subcomponent of the analysis.

3. *Execute your workflow.* From the same directory as the ``flo.yaml``
   file (or any child directory), execute ``flo run`` and this will run
   each task defined in your ``flo.yaml`` until everything is complete.
   If any task definition in the ``flo.yaml`` or the contents of its
   dependencies change, re-running ``flo run`` will only redo the parts
   of the workflow that are out of sync since the last time you ran it.
   The ``flo`` command has `several other convenience
   options <#command-line-interface>`__ to facilitate quickly writing
   data workflows. Running the `hello-world
   example <examples/hello-world>`__ for the first time yields something
   like this:

   .. figure:: http://i.imgur.com/WZsUJNN.png
      :alt: hello world screenshot

4. *Repeat steps 2-3 until your data workflow is complete.* When
   developing a data workflow, it is common to write an entire workflow
   and then go back and revisit particular parts of the analysis. The
   entire purpose of this package is to make it easy to refine task
   definitions and quickly re-run workflows with confidence that the
   user will not ruin previous results or start a simulation that takes
   a long time.
