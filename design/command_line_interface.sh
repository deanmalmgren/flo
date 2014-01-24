# The goal here is to try and write down what the ideal command line
# interface should look like. This is not intended to be exhaustive,
# but a good starting point to highlight typical use cases. For now,
# I'll assume the command that this all sits under is called
# `workflow`

# By default, execute entire workflow, or at least the portion of it
# that is "out of sync". When you edit a particular file in the
# workflow and rerun `workflow`, this should only re-execute the parts
# that been affected by the change. This makes it very easy to iterate
# quickly on data analysis problems without having to worry about
# re-running an arsenal of data analysis tasks.
workflow
nano path/to/some/file
workflow


# Sometimes, you've made a dramatic change and you want to re-run an
# entire workflow, ignoring the sha hash state of every file. This can
# also be useful when you want to rerun an analysis periodically after
# the original data set has changed
workflow --force


# Another common use case is to just delete the entire workflow
# without rerunning anything. This should delete all targets that are
# defined in the workflow; anything that matches a `creates` in
# `workflow.yaml`. BEFORE deleting everything, this should verify that
# a user actually wants to remove all these files.
workflow --clean


# Similar to above, but do not require a user to verify that they want
# to delete everything
workflow --force-clean


# Another common use case during development is to run the workflow up
# to a partiuclar step to make sure that intermediate results make
# sense. This just runs the workflow up to and including the
# data/result.png. After editing a file that renders the result, it
# should only re-run the last step.
workflow data/result.png
nano src/render_result.py
workflow data/result.png


# Can also run more than one target from the command line, if that is
# easier
workflow data/result.png data/download.tgz


# Sometimes you end up editing several files and, before you run the
# workflow, you want to see the set of steps that are going to be run
# *without* actually running them to make sure you aren't going to
# redo a step that will take a long time. This could even try to
# estimate how long the process will take?
nano path/to/a/file
nano path/to/another/file
nano path/to/some/file
workflow --dry-run


# This is something that drives me crazy about GNU make --- you should
# be able to run a workflow from any subdirectory whose ancestor
# contains a workflow.yaml file, the same way Fabric works with
# fabfiles or mercurial/git work with .hg/.git directories
cd path/to/a
nano file
workflow


# When you change a workflow.yaml target in the yaml file itself, this
# should also trigger the necessary parts to be rerun. `workflow` must
# be smart enough to detect when targets have changed. In this
# example, the first execution of `workflow` runs the entire workflow
# to completion. Then the user edits a particular target in the
# workflow.yaml file. The second execution of `workflow` only runs the
# parts of the workflow that are affected by the changes.
workflow
nano workflow.yaml
workflow


# to expedite development and iteration, it is often
# possible/advantageous to write targets that are run once per input
# file. To help with development in these situations, you often want
# to iterate on that element on the workflow on only one file, instead
# of all input files (see data/per_file target in workflow.yaml)
workflow data/per_file --filename-root=a_specific_filename


# another way to expedite development and iteration is to limit the
# amount of time that each step takes. Should this be on a per-step
# basis or a total-time basis?
workflow data/per_file --time-limit=1s
