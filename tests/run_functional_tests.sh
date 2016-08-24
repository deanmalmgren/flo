#!/bin/bash

# this script runs a few functional tests to make sure that everything
# is working properly. on error in any subcommands, it should not quit
# and finally exit with a non-zero exit code if any of the commands
# failed

# get the directory of this script and use it to correctly find the
# examples directory
# http://stackoverflow.com/a/9107028/564709
BASEDIR=$(cd `dirname "${BASH_SOURCE[0]}"` && pwd)
EXAMPLE_ROOT=$BASEDIR/../examples

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

# function to update exit code and throw error if update value is
# non-zero
EXIT_CODE=0
update_status () {
    if [[ $1 -ne 0 ]]; then
	red "$2"
    fi
    EXIT_CODE=$(expr ${EXIT_CODE} + $1)
}

# function for running test on a specific example to validate that the
# checksum of results is consistent
validate_example () {
    example=$1
    test_checksum=$2
    cd ${EXAMPLE_ROOT}/${example}
    flo clean --force --include-internals
    update_status $? "thorough cleaning didn't work in validate_example"
    flo run
    update_status $? "run didn't work in validate_example"
    flo archive --exclude-internals
    update_status $? "archiving didn't in validate_example"

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
	update_status 1 ""
    fi
}

# run a few examples to make sure the checksums match what they are
# supposed to. if you update an example, be sure to update the
# checksum by just running this script and determining what the
# correct checksum is
validate_example hello-world 040bf35be21ac0a3d6aa9ff4ff25df24
validate_example model-correlations c2e4ae57ff2d970a076b364bab87a87f

# this runs specific tests for the --start-at option
cd $BASEDIR
python test_start_at.py ${EXAMPLE_ROOT}
update_status $? "--start-at tests failed"

# test the --skip option to make sure everything works properly by
# modifying a specific task that would otherwise branch to other tasks
# and make sure that skipping it does not trigger the workflow to run
cd ${EXAMPLE_ROOT}/model-correlations
flo run --force
sed 's/\+1/+2/g' flo.yaml > new_flo.yaml
mv flo.yaml old_flo.yaml
mv new_flo.yaml flo.yaml
flo run --skip data/x_y.dat
grep "No tasks are out of sync" .flo/flo.log > /dev/null
update_status $? "Nothing should have been run when --skip'ping changed task"
flo run
grep "|-> cut " .flo/flo.log > /dev/null
update_status $? "data/x_y.dat command was not re-run even though it changed"
mv old_flo.yaml flo.yaml
cd ${EXAMPLE_ROOT}

# test the --only option
cd ${EXAMPLE_ROOT}/hello-world
flo run --force
flo run --only data/hello_world.txt
grep "No tasks are out of sync" .flo/flo.log > /dev/null
update_status $? "data/hello_world.txt shouldn't have been run"
flo run -f --only data/hello_world.txt
n_matches=$(grep "|-> " .flo/flo.log | wc -l)
if [[ ${n_matches} -ne 2 ]]; then
    msg="flo run -f --only data/hello_world.txt should only run two commands"
    update_status 1 "$msg"
fi
cd ${EXAMPLE_ROOT}

# make sure that flo always runs in a deterministic order
cd ${EXAMPLE_ROOT}/deterministic-order
flo clean --force
update_status $? "force cleaning failed on deterministic-order example"
flo run --force
update_status $? "deterministic-order example failed somewhere along the way"
sed -n '/|-> /{g;1!p;};h' .flo/flo.log | sort -c
update_status $? "flo not running in expected deterministic order"
cd ${EXAMPLE_ROOT}

# make sure flo runs equally well with non-standard config
# files. first run this example using the standard issue flo.yaml and
# then run it with a slightly modified version to make sure everything
# works just fine with more than one config file in the directory
cd $EXAMPLE_ROOT/hello-world
sed -e 's/\(.*\).dat$/\1.dat.alt/' -e 's/\(.*\).txt$/\1.txt.alt/' flo.yaml > alt.yaml
flo run -f
update_status $? "running flo with standard flo.yaml failed"
flo run -c alt.yaml
update_status $? "running flo with standard alt.yaml failed"
for f in data/*.alt; do
    g=$(dirname $f)/$(basename $f .alt)
    diff $g $f
    update_status $? "results from alt.yaml (${f}) and flo.yaml (${g}) differ"
done
flo clean -fc alt.yaml
update_status $? "cleaning from alt.yaml failed"
update_status $(find . -name "*.alt" | wc -l) "files named *.alt still exist"
rm alt.yaml
cd $EXAMPLE_ROOT

# exit with the sum of the status
exit ${EXIT_CODE}
