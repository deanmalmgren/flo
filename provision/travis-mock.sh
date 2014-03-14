#!/bin/bash

# these additional packages are required to make the virtual machine
# have a similar environment to travis-ci before we install anything
# else.  See Vagrantfile for details on how this could be done better
# if its a problem.
# http://docs.travis-ci.com/user/languages/python/#Travis-CI-Uses-Isolated-virtualenvs
sudo apt-get update
sudo apt-get install -y python-pip python-dev build-essential
