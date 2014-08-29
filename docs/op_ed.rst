.. _op-ed:

op-ed
-----

We built ``flo`` because :ref:`existing tools <prior-art>` were not
cutting it for us and we kept finding ourselves saying things like:

    "It should be easy to swap in development data for production data."
    - `@bo_p <http://twitter.com/bo_p>`__

    "It should be easy to work on one file at a time." - `@mstringer
    <http://twitter.com/mstringer>`__

    "It should be easy to avoid making costly mistakes." -
    `@deanmalmgren <http://twitter.com/deanmalmgren>`__

There are many ways one could conceivably write a data analysis workflow
from scratch, from writing single programs that ingest, analyze and
visualize data to simple scripts that each handle one part of the
puzzle. Particularly when developing workflows from scratch, we have the
strong opinion that writing small scripts with intermediate outputs is a
much more effective way to develop a prototype data workflow. In our
experience, we find it to be very convenient to edit a script, run it,
and repeat several times to make sure it is behaving the way we intend.
For one thing, this pattern makes it far easier to spot check results
using a litany of available command line tools. For another, this
pattern makes it easy to identify weak links (*e.g.* incorrect results,
poor performance, etc.) in the analysis and improve them piece by piece
after the entire workflow has been written the first time.

.. _design-goals:

design goals
~~~~~~~~~~~~

This package is deliberately designed to help users write small, but
compact workflow prototypes using whatever tools they prefer --- R,
pandas, scipy, hadoop. The goal here is not to provide a substitute
for these tools, but rather to be the glue that sticks them
together. It takes inspiration from a number of :ref:`existing tools
<prior-art>` that have similar aims, particularly :ref:`gnu-make` that
has `many desirable properties of working with data workflows
<http://bost.ocks.org/mike/make/>`__. Specifically, the design goals
for this project are to:

*  *Provide an easy-to-use framework.* This applies for n00bs and pros
   alike. Use human-readable syntax.
*  *Prevent, as much as reasonably possible, costly mistakes.* Avoid
   inadvertently rerunning commands that overwrite results or executing
   commands that take a long time.
*  *Encourage good development practices, but allow for flexibility.*
   There's a tradeoff here, but we have :ref:`an opinion <op-ed>` on how
   to do this in a good way.

.. _prior-art:

prior art
~~~~~~~~~

.. _GNU-make:

GNU make
''''''''

`GNU make <http://www.gnu.org/software/make/>`__ is a very useful tool
that was designed mostly for building complicated software packages. It
works particularly well when you are compiling a bunch of ``.c`` or
``.h`` files into ``.o`` files because you can use rules to define how
``.o`` files are created from a bunch of dependencies (and usually not
too many of them). I've used this `to manage data
workflows <http://bost.ocks.org/mike/make/>`__ too and, provided you're
only working by yourself and you are comfortable with its arcane file
format, make is a great tool. A few things make ``make`` less
desireable, particularly for managing data workflows that tend to take
hours or days rather than minutes.

-  ``make`` uses timestamps, instead of hashes, to determine when a file
   is out of date with the rest. This isn't so terrible, except when
   you're working in an asynchronous development environment with ``hg``
   or ``git`` that does not version the timestamp of files.

-  ``Makefile``\ s are extraordinarily picky and not terribly easy for
   n00bs to use. Even for those that are fluent in ``Makefile``, looking
   over a Makefile is pretty cumbersome and not easy to read. This is a
   downer when you're trying to rapidly develop.

-  ``make`` does not run in parallel or, if it does, it requires a
   deeper understanding of its arcane format than I am comfortable with.
   Particularly with data workflows that can potentially take days to
   complete, this is a very undesireable behavior.

-  ``make`` is filesystem based, but doesn't have the ability to test
   whether databases or cloud storage has been updated. This is pretty
   important for data workflows.

invoke
''''''

`Invoke <http://docs.pyinvoke.org/en/latest/>`__ is intended to be a
make replacement for python with a nice Fabric-like command line
interface. It is function/class based rather than file based and,
because its in python, you can basically do anything you need to within
an ``invoke`` script. Downsides include:

-  Because its function/class based, there is a lot of syntactic bloat
   that does not make invoke scripts considerably longer than they need
   to be.

-  Although ``invoke`` does provide a `'pre' keyword argument
   <http://docs.pyinvoke.org/en/latest/concepts/execution.html#pre-tasks>`__,
   it is not possible to run an invoke script without rerunning the
   *entire* workflow (`git issue here
   <https://github.com/pyinvoke/invoke/issues/100>`__). Although its
   certainly possible to extend invoke to address this use case, its
   not clear that it'll be enough to address all the use cases that we
   have in mind.

Fabric
''''''

`Fabric <http://docs.fabfile.org/en/latest/>`__ is a tool that is
intended for application deployment to many different servers
simultaneously. It has a great command-line interface for deployment and
DevOps, but doesn't provide a lot of out-of-the box functionality for
managing data workflows. Downsides include:

-  Fabric parallelizes tasks across machines, not tasks. In data
   analysis situations, you can actually divvy up analysis tasks
   depending on what data files are or not available.

-  ``fabfile``\s tend to get big rather quickly, even for relatively
   mundane jobs. The fact that its in python is nice, but probably not
   necessary for running a data analysis workflow.

-  There is no default way of detecting whether a task needs to be run
   based on timestamps or hashes. Its certainly possible to extend
   Fabric to address this issue.

Drake
'''''

`Drake <https://github.com/Factual/drake>`__ is intended to be the "make
for data". ``Drakefile``\ s have `a very similar look and
feel <https://github.com/Factual/drake/wiki/Tutorial>`__ of
``Makefile``\ s. It has some pretty decent advantages over ``make`` in
that it comes pre-equipped with
`parallelization <https://github.com/Factual/drake/wiki/Async-Execution-of-Steps>`__
and with filesystem, S3 and HDFS integration, but there are a few key
disadvantages:

-  `It is based on
   timestamps <https://docs.google.com/document/d/1bF-OKNLIG10v_lMes_m4yyaJtAaJKtdK0Jizvi_MNsg/edit#heading=h.30j0zll>`__.
   This makes it tricky to develop when working in an asynchronous
   development environment like ``hg`` or ``git``.

-  Its written in clojure, which makes it difficult for most data people
   to contribute too (?), or at least difficult for this data person to
   read.

AWS Data Pipeline
'''''''''''''''''

`Amazon's Data Pipeline <http://aws.amazon.com/datapipeline/details/>`__
is intended to organize data pipelines that occur entirely in Amazon's
cloud. This seems extremely handy if you're playing entirely within
Amazon's walls, but not terribly convenient for a wide range or projects
where a cloud solution is unnecessarily overkill.

LONI Pipeline
'''''''''''''

Meh. http://pipeline.bmap.ucla.edu/

Predictive Modeling Markup Language (PMML)
''''''''''''''''''''''''''''''''''''''''''

PMML is a language to define workflows in data analysis. There appear to
be many tools that will execute PMML workflows, for example
`Augustus <https://code.google.com/p/augustus/>`__ and
`Zementis <http://aws.amazon.com/customerapps/1583?_encoding=UTF8&jiveRedirect=1>`__
for executing on Amazon Web Services. It appears to be geared more
toward developing robust, "enterprise" workflows as opposed to rapid
development.

Tez
'''

`Tez <http://tez.apache.org/>`__ appears to be the Hadoop equivalent of
creating data workflows using `YARN
<http://hadoop.apache.org/docs/current/hadoop-yarn/hadoop-yarn-site/YARN.html>`__.
If you're nuts about java and everything you do is in hadoop, this is
probably great for you.

KNIME
'''''

`KNIME <http://www.knime.org/>`__ is a graphical interface for
defining data *and* analysis steps in a data workflow. I'm sure its
possible to write custom analysis steps in KNIME to make it more
practical in real world situations, but the tight coupling between the
pipeline definition and actually running an analysis and doing some
visualization is highly unappealing for the use cases I have in
mind. Nonetheless, its worth mentioning. The GUI is admittedly kinda
nice and certainly easier to understand for n00bs.


