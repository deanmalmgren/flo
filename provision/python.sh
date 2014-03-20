#!/bin/bash

# this needs to work both for vagrant provisioning and for travis
# builds in a python virtualenv. in the virtual machine provisioning,
# we're passing the directory this should be run from. in travis-ci,
# its run from the root of the repository.
if [ "$#" -eq 1 ]; then
    cd $1
fi

# install the requirements for this package as well as this module.
pip install -r REQUIREMENTS
pip install .

# install the requirements for running the examples
pip install -r examples/REQUIREMENTS

# setup global argcomplete
# https://github.com/kislyuk/argcomplete#activating-global-completion
activate-global-python-argcomplete --dest /etc/bash_completion.d/
