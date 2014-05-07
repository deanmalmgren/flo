changelog
=========

Backwards incompatible features are highlighted in **bold**.


latest
------

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
