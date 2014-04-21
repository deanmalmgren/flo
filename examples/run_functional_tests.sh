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
    flo clean --force --include-internals
    exit_code=$(expr ${exit_code} + $?)
    flo run
    exit_code=$(expr ${exit_code} + $?)
    flo archive --exclude-internals
    exit_code=$(expr ${exit_code} + $?)

    # hack to compute checksum of resulting archive since tarballs of
    # files with the same content are apparently not guaranteed to
    # have the same md5 hash
    temp_dir=/tmp/${example}
    mkdir -p ${temp_dir}
    tar -xf .flo/archive/* -C ${temp_dir}
    local_checksum=$(find ${temp_dir}/ -type f | sort | xargs cat | md5)
    rm -rf ${temp_dir}
    if [ "${local_checksum}" != "${test_checksum}" ]; then
        red "ERROR--CHECKSUM OF ${example} DOES NOT MATCH"
        red "    local checksum=${local_checksum}"
        red "     test checksum=${test_checksum}"
        exit_code=$(expr ${exit_code} + 1)
    fi
    cd $BASEDIR
}

# run a few examples to make sure the checksums match what they are
# supposed to. if you update an example, be sure to update the
# checksum by just running this script and determining what the
# correct checksum is
validate_example hello-world 040bf35be21ac0a3d6aa9ff4ff25df24
validate_example model-correlations 14ba1ffc4c37cd306bf415107d6edfd1

# this runs specific tests for the --start-at option
python test_start_at.py
exit_code=$(expr ${exit_code} + $?)

# test the --skip option to make sure everything works properly by
# modifying a specific task that would otherwise branch to other tasks
# and make sure that skipping it does not trigger the workflow to run
cd $BASEDIR/model-correlations
flo run -f
sed -i 's/\+1/+2/g' flo.yaml
flo run --skip data/x_y.dat
grep "No tasks are out of sync" .flo/flo.log > /dev/null
exit_code=$(expr ${exit_code} + $?)
flo run
grep "|-> cut " .flo/flo.log > /dev/null
exit_code=$(expr ${exit_code} + $?)
sed -i 's/\+2/+1/g' flo.yaml
cd $BASEDIR

# test the --only option
cd $BASEDIR/hello-world
flo run -f
flo run --only data/hello_world.txt
grep "No tasks are out of sync" .flo/flo.log > /dev/null
exit_code=$(expr ${exit_code} + $?)
flo run -f --only data/hello_world.txt
n_matches=$(grep "|-> " .flo/flo.log | wc -l)
if [[ ${n_matches} -ne 2 ]]; then
    red "flo run -f --only data/hello_world.txt should only run two commands"
    exit_code=$(expr ${exit_code} + 1)
fi
cd $BASEDIR

# exit with the sum of the status
exit ${exit_code}
