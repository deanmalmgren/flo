The purpose here is to give a bare bones example of a workflow that
doesn't even have any source code --- all of the necessary commands
are embedded in `flo.yaml`. This is important because
[`flo` detects changes to the `flo.yaml` file](../../#flo-run). To see
this in action, execute `flo run` in this directory from the command
line, then modify any of the tasks defined in `flo.yaml` to confirm
that those tasks (and any affected downstream tasks) are re-run when
you execute `flo run` again.
