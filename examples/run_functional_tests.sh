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
which md5 > /dev/null
if [ $? -ne 0 ]; then
    md5 () {
	md5sum $1 | awk '{print $1}'
    }
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
    workflow clean --force --include-internals
    exit_code=$(expr ${exit_code} + $?)
    workflow run
    exit_code=$(expr ${exit_code} + $?)
    workflow archive --exclude-internals
    exit_code=$(expr ${exit_code} + $?)

    # hack to compute checksum of resulting archive since tarballs of
    # files with the same content are apparently not guaranteed to
    # have the same md5 hash
    temp_dir=/tmp/${example}
    mkdir -p ${temp_dir}
    tar -xf .workflow/archive/* -C ${temp_dir}
    local_checksum=$(find ${temp_dir}/ -type f | sort | xargs cat | md5)
    rm -rf ${temp_dir}
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
validate_example hello-world fb8915998f1095695ec34bc579bb41e6
validate_example model-correlations c7a09e0a30c20a731ef6112591e697e3
#validate_example reuters-tfidf 211d66460dd680a79211cf0521bb4445

md5sum $BASEDIR/model-correlations/workflow.yaml
md5sum $BASEDIR/model-correlations/data/*
md5sum $BASEDIR/model-correlations/src/*

# exit with the sum of the status
exit ${exit_code}
