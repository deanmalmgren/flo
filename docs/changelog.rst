changelog
=========

This project uses `semantic versioning <http://semver.org/>`__ to
track version numbers, where backwards incompatible changes
(highlighted in **bold**) bump the major version of the package.


latest
------

* enforce that ``depends`` must exist prior to running any commands (#59)

* more informative error messages (#56, #57, #58)

* several bug fixes, including:

  * properly handling backspacing output of subprocessed commands (#53)

1.0.0
-----

* **removed pseudotask creation** (every task must have a ``command`` key)

* specifying alternative yaml configuration (#62)

* incorporated deterministic ordering in a predictable and explainable
  manner (#65, #70)

* introduced ``flo status`` command; **removed ``flo run --dry-run``
  in favor of ``flo status``** (#55)

* incorporated the ``--only`` option (#37)

* several bug fixes, including:

  * making sure that the TaskGraph is a directed acyclic graph (#61)

  * ensuring that ``creates`` exists after a task has been run (#60)

  * clarifying output on ``flo status`` and ``flo run`` (#64)

0.2.0
-----

* Initial release
