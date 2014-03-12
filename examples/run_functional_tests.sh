#!/bin/bash

# this script runs a few functional tests to make sure that everything
# is working properly. on error in any subcommands, it should not quit
# and finally exit with a non-zero exit code if any of the commands
# failed
exit_code=0

# get the directory of this script
# http://stackoverflow.com/a/9107028/564709
BASEDIR=$(cd `dirname "${BASH_SOURCE[0]}"` && pwd)

# annoying problem that md5 (OSX) and md5sum (Linux) are not the same
# in coreutils
MD5=md5
which md5 > /dev/null
if [ $? -ne 0 ]; then
    MD5=md5sum
fi

# formatting functions
red () { 
    echo $'\033[31m'"$1"$'\033[0m'
}

# function for running test on a specific example to validate that the
# checksum of results is consistent
validate_example () {
    example=$1
    test_checksum=$2
    cd $BASEDIR/${example}
    workflow -fc
    exit_code=$(expr ${exit_code} + $?)
    workflow
    exit_code=$(expr ${exit_code} + $?)
    local_checksum=$(cat workflow.yaml */* | md5)
    if [ "${local_checksum}" != "${test_checksum}" ]; then
	red "ERROR--CHECKSUM OF ${example} DOES NOT MATCH"
	red "    local checksum=${local_checksum}"
	red "     test checksum=${test_checksum}"
	exit_code=$(expr ${exit_code} + 1)
    fi
}

# run a few examples to make sure the checksums match what they are
# supposed to. if you update an example, be sure to update the
# checksum by just running this script and determining what the
# correct checksum is
validate_example hello-world 1027ea472a2c1050bfbded4994677478
validate_example model-correlations abfeb32f33b2049af8f63a19aa77911b

# exit with the sum of the status
exit ${exit_code}
