#!/bin/bash

sudo apt-get install -y curl unzip

# these are technically in the examples/REQUIREMENTS, too, but
# installing dependencies is a bit of a pain in the ass so use this to
# get all the dependencies first before rebuilding latest using pip.
sudo apt-get install -y python-numpy python-matplotlib
