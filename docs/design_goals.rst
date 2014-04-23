design goals
~~~~~~~~~~~~

This package takes inspiration from a number of `existing
tools <design/prior_art.md>`__ that have similar aims, particularly `GNU
make <http://www.gnu.org/software/make/>`__ that has `many desirable
properties of working with data
workflows <http://bost.ocks.org/mike/make/>`__. Specifically, the design
goals for this project are to:

-  *Provide an easy-to-use framework.* This applies for n00bs and pros
   alike. Use human-readable syntax.
-  *Prevent, as much as reasonably possible, costly mistakes.* Avoid
   inadvertently rerunning commands that overwrite results or executing
   commands that take a long time.
-  *Encourage good development practices, but allow for flexibility.*
   There's a tradeoff here, but we have `an opinion <#op-ed>`__ on how
   to do this in a good way.

Many of these concepts have been captured in the original road map for
`flo.yaml <design/flo.yaml>`__ and the `command line
interface <design/command_line_interface.sh>`__ design specification.
Most of these concepts have been implemented or are on the road map, but
if you have any suggestions for other ideas, please `add
them <issues>`__!
