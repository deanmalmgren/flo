developing
~~~~~~~~~~

1. `Fork <https://github.com/deanmalmgren/flo/fork>`__ and clone the
   project:

   .. code-block:: bash

        git clone https://github.com/YOUR-USERNAME/flo.git

2. Install `Vagrant <http://vagrantup.com/downloads>`__ and
   `Virtualbox <https://www.virtualbox.org/wiki/Downloads>`__ and launch
   the development virtual machine:

   .. code-block:: bash

        vagrant up && vagrant provision

   On ``vagrant ssh``\ ing to the virtual machine, note that the
   ``PYTHONPATH`` and ``PATH`` `environment variables have been
   altered in this virtual machine
   <https://github.com/deanmalmgren/flo/blob/master/provision/development.sh>`__
   so that any changes you make to your local data workflow scripts
   are automatically reloaded.

3. On the virtual machine, make sure everything is working by executing
   workflows in ``examples/*/flo.yaml``

   .. code-block:: bash

        cd examples/reuters-tfidf
        flo run

4. To be more thorough, there is an automated suite of functional tests
   to make sure any patches you have made haven't disturbed the behavior
   of this package in any substantiative way.

   .. code-block:: bash

        ./tests/run_functional_tests.sh

   These functional tests are designed to be run on an Ubuntu 12.04
   LTS server, just like the virtual machine and the server that runs
   the travis-ci test suite. There are some other tests that have been
   added along the way in the `Travis configuration
   <https://github.com/deanmalmgren/flo/blob/master/.travis.yml>`__. For your
   convenience, you can run all of these tests with:

   .. code-block:: bash

        ./tests/run.py

   Current build status: |Build Status|

5. Contribute! There are several `open issues
   <https://github.com/deanmalmgren/flo/issues>`__ that provide good
   places to dig in. Check out the `contribution guidelines
   <https://github.com/deanmalmgren/flo/blob/master/CONTRIBUTING.md>`__ and send
   pull requests; your help is greatly appreciated!

.. |Build Status| image:: https://travis-ci.org/deanmalmgren/flo.png
   :target: https://travis-ci.org/deanmalmgren/flo
