#!/bin/bash

# this script runs a few functional tests to make sure that everything
# is working properly. on error in any subcommands, it should not quit
# and finally exit with a non-zero exit code if any of the commands
# failed
exit_code=0

# get the directory of this script
# http://stackoverflow.com/a/9107028/564709
BASEDIR=$(cd `dirname "${BASH_SOURCE[0]}"` && pwd)

# run the hello-world example and make sure it has the same results as
# what is archived in our test archive
cd $BASEDIR/hello-world
workflow -fc
exit_code=$(expr ${exit_code} + $?)
workflow
exit_code=$(expr ${exit_code} + $?)

# run the model-correlations example and make sure it has the same
# results as what is archived in our test archive
cd $BASEDIR/model-correlations
workflow -fc
exit_code=$(expr ${exit_code} + $?)
workflow
exit_code=$(expr ${exit_code} + $?)

# exit with the sum of the status
exit ${exit_code}
