#!/bin/bash

# get the base directory name of this file
# http://stackoverflow.com/a/11114547/564709
sudo apt-get install -y realpath
base=$(dirname $(realpath $0))/..

# install all of the dependencies required in the examples
sed 's/\(.*\)\#.*/\1/' < $base/examples/DEBIAN | xargs sudo apt-get install -y
