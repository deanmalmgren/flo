.. _design-goals:

design goals
~~~~~~~~~~~~

This package takes inspiration from a number of :ref:`existing tools
<prior-art>` that have similar aims, particularly :ref:`gnu-make` that
has `many desirable properties of working with data workflows
<http://bost.ocks.org/mike/make/>`__. Specifically, the design goals
for this project are to:

-  *Provide an easy-to-use framework.* This applies for n00bs and pros
   alike. Use human-readable syntax.
-  *Prevent, as much as reasonably possible, costly mistakes.* Avoid
   inadvertently rerunning commands that overwrite results or executing
   commands that take a long time.
-  *Encourage good development practices, but allow for flexibility.*
   There's a tradeoff here, but we have :ref:`an opinion <op-ed>` on how
   to do this in a good way.
