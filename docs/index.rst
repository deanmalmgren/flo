.. flo documentation master file, created by
   sphinx-quickstart on Wed Apr 23 19:42:51 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

op-ed
~~~~~

    "It should be easy to swap in production data for development data."
    - @bo-peng

    "It should be easy to work on one file at a time." - @stringertheory

    "It should be easy to avoid making costly mistakes." - @deanmalmgren

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

This package is deliberately designed to help users write small, but
compact workflow prototypes using whatever tools they prefer --- R,
pandas, scipy, hadoop. The goal here is not to provide a substitute for
these tools, but rather to be the glue that sticks them together.

.. toctree::
   quick_start
   yaml_specification
   command_line_interface
   design_goals
   prior_art
   developing
   :maxdepth: 2



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

