### op-ed

> "It should be easy to swap in production data for development
> data." -@bo-peng

> "It should be easy to work on one file at a time." -@stringertheory

> "It should be easy to avoid making costly mistakes." -@deanmalmgren

There are many ways one could conceivably write a data analysis
workflow from scratch, from writing single programs that ingest,
analyze and visualize data to simple scripts that each handle one part
of the puzzle. Particularly when developing workflows from scrach, we
have the strong opinion that writing small scripts with intermediate
outputs is a much more effecitve way to develop a prototype data
workflow. In our experience, we find it to be very convenient to edit
a script, run it, and repeat several times to make sure it is behaving
the way we intend. For one thing, this pattern makes it far easier to
spot check results using a litany of available command line tools. For
another, this pattern makes it easy to identify weak links (*e.g.*
incorrect results, poor performance, etc.) in the analysis and improve
them piece by piece after the entire workflow has been written the
first time.

This packages is deliberately intended to help users write small, but
compact workflow prototypes using whatever tools they prefer (R,
pandas, scipy, hadoop) but with the explicit goal of encouraging users
to write small scripts that produce intermediate output.

The goal of this project is to make it easy to quickly *develop* data
workflows with any tool set you want --- pandas, R, matlab, scipy,
hadoop, etc. The goal here is not to provide a substitute for these
tools, but rather to be the glue that sticks them together.

### quick start

1. *Install this pacakge.* `pip install data-workflow` XXXX NEED TO GET THIS TO WORK

2. *Write a workflow.yaml.* Create a `workflow.yaml` file in the root
   of your project. `workflow.yaml` can
   [have many features](#workflowyaml-specification), but the basic
   idea is to make it easy to quickly define a sequence of dependent
   tasks in an easy-to-read way. There are several
   [examples](examples/), the simplest of which is the
   [hello-world example](examples/hello-world/workflow.yaml). Briefly,
   every task is a YAML object that has a `creates` key that
   represents the resource that is created by this task and a
   `command` key that defines the command that are required to create
   the resource defined in `creates`. You can optionally define a
   `depends` key that lists resources, either filenames on disk or
   other task `creates` targets, to quickly set up dependency chains.

3. *Execute your workflow.* From the same directory as the
   `workflow.yaml` file (or any child directory), run `workflow` and
   this will run each task defined in your `workflow.yaml` until
   everything is complete. If any task definition in the
   `workflow.yaml` or the contents of its dependencies change,
   re-running `workflow` will only redo the parts of the workflow that
   are out of sync since the last time you ran it. The `workflow`
   command has
   [several other convenience options](#command-line-interface) to
   facilitate quickly writing data workflows.

4. *Repeat steps 2-3 until your data workflow is complete.* When
   developing a data workflow, it is common to write an entire
   workflow and then go back and revisit particular parts of the
   analysis. The entire purpose of this package is to make it easy to
   refine task definitions and quickly re-run workflows with
   confidence that the user will not ruin previous results or start a
   simulation that takes a long time.

### workflow.yaml specification

Individual analysis tasks are defined as
[YAML objects](http://en.wikipedia.org/wiki/YAML#Associative_arrays)
in `workflow.yaml` with something like this:

```yaml
---
creates: path/to/some/output/file.txt
depends: path/to/some/script.py
alias: awesome
command: python {{depends}} > {{creates}}
```

Every task YAML object must have a `creates` key and a `command` key
and can optionally contain `alias` and `depends` keys. The order of
these keys does not matter; the above order is chosen for explanatory
purposes only.

**`creates`.** The `creates` key defines the resource that is
created. By default, it is interpretted as a path to a file (relative
paths are interpretted as relative to the `workflow.yaml` file). You
can also specify a protocol, such as `mysql:database/table` (see
yet-to-be-implemented #15), for non-file based resources.

**`depends`.** The `depends` key defines the resource(s) on which this task
depends. It is common for `depends` to specify many things, including
data analysis scripts or other tasks from within the
`workflow.yaml`. Multiple dependencies can be defined in a
[YAML list](http://en.wikipedia.org/wiki/YAML#Lists) like this:

```yaml
depends:
  - path/to/some/script.py
  - another/task/creates/target.txt
```

**`alias`.** The `alias` key specifies an alternative name that can be used to
specify this task as a `depends` in other parts of the workflow or on
the command line.

**`command`.** The `command` key defines the command(s) that should be
executed to produce the resource specified by the `creates` key.  Like
the `depends` key, multiple steps can be defined in a
[YAML list](http://en.wikipedia.org/wiki/YAML#Lists) like this:

```yaml
command:
  - mkdir -p $(dirname {{creates}})
  - python {{depends}} > {{creates}}
```

**templating variables.** Importantly, the `command` is rendered as a
[jinja template](http://jinja.pocoo.org/) to avoid duplication of
information that is already defined in that task. Its quite common to
use `{{depends}}` and `{{creates}}` in the `command` specification,
but you can also use other variables like this:

```yaml
---
creates: path/to/some/output/file.txt
sigma: 2.137
depends: path/to/some/script.py
command python {{depends}} {{sigma} > {{creates}}
```

In the aforementioned example, `sigma` is only available when rendering
the jinja template for that task. If you'd like to use `sigma` in
several other tasks, you can alternatively put it in a global
namespace in a workflow.yaml like this
([similar example here]("examples/model-correlations")):

```yaml
---
sigma: 2.137
tasks: 
  - 
    creates: path/to/some/output/file.txt
    depends: path/to/some/script.py
    command python {{depends}} {{sigma} > {{creates}}
  -
    creates: path/to/another/output/file.txt
    depends:
	  - path/to/another/script.py
      - path/to/some/output/file.txt
    command: python {{depends[0]}} {{sigma}} < {{depends[1]}} > {{creates}}
```

There are several [examples](examples/) for more inspiration on how
you could use this. If you have suggestions for other ideas, please
[add them](issues)!

### command line interface

This package ships with the `workflow` command, which embodies the
entire command line interface for this package. This command can be
run from the directory that contains `workflow.yaml` or any of its
child directories.

By default, running `workflow` will execute the entire workflow, or at
least the portion of it that is "out of sync" since the last time it
ran. Running `workflow` twice in a row without editing any files in
the interim will not rerun any steps. If you edit a particular file in
the workflow and rerun `workflow`, this will only re-execute the parts
that have been affected by the change. This makes it very easy to
iterate quickly on data analysis problems without having to worry
about re-running an arsenal commands --- you only have to remember
one, `workflow`.

```bash
workflow                    # runs everything for the first time
workflow                    # nothing changed; runs nothing
edit path/to/some/script.py
workflow                    # only runs the parts that are affected by change
```

Importantly, if you edit a particular task in the `workflow.yaml`
itself, this will cause that particular task to be re-run as well:

```bash
workflow
edit workflow.yaml          # change a particular task's command
workflow                    # rerun's that command and any dependent task
```

The `workflow` command is able to do this by tracking the status of
all `creates`, `depends`, and task definitions by hashing the contents
of these resources. If the contents in any `depends` or the task
itself has changed since the last time that task was run, `workflow`
will run that task. For reference, the hashes of all of the `creates`,
`depends`, and workflow task definitions are in `.workflow/state.csv`.

**specify a particular task.** Oftentimes we do not want to run the
entire workflow, but only a particular component of it. Like GNU make,
you can specify a particular task (either by its `alias` or its
`creates`) on the command line like this:

```bash
workflow path/to/some/output/file.txt
```

This limits `workflow` to only executing the task defined in
`path/to/some/output/file.txt` and all of its recursive upstream
dependencies.

**`--clean` and `--force`.** Sometimes you want to start with a clean
slate. Perhaps the data you originally started with is dated or you
want to be confident a workflow properly runs from start to finish
before inviting collaborators. Whatever the case, the `--clean` option
can be useful for removing all `creates` targets that are defined in
`workflow.yaml` and the `--force` option can be useful for just
rerunning all steps, regardless of whether they are out of date.

```bash
workflow --clean            # asks user if they want to remove `creates` results
workflow --force            # rerun entire workflow
```

**`--backup` and `--restore`.** Before removing or totally redoing an
analysis, I've often found it useful to backup my results and compare
the differences later. The `--backup` and `--restore` command line
options make it easy to quickly backup an entire workflow (including
generated `creates` targets, source code specified in `depends`, and
the underlying `workflow.yaml`) and compare it to previous versions.

```bash
workflow --backup           # store archive in .workflow/archives/*.tar.bz2
for i in `seq 20`; do
	edit path/to/some/script.py
	workflow
done
echo 'oh crap, this sequence of changes was a mistake'
workflow --restore          # uncompresses archive
```

**`--dry-run`.** While [we don't recommend it](#op-ed), its not
uncommon to get "in the zone" and make several edits to analysis
scripts before re-running your workflow. Because we're human, its easy
to incorrectly remember the files you edited and how they may affect
re-running the workflow. To help, the `--dry-run` option lets you see
which commands will be run and approximately how much time it should
take (!!!).

```bash
workflow
edit path/to/some/script.py
edit path/to/another/script.py
workflow --dry-run         # don't run anything, just report what would be done
```

For reference, `workflow` stores the duration of each task in
`.workflow/duration.csv`.

**`--export`.** Sometimes you just want a shell script, plain and
simple. The `--export` option makes it easy to quickly export the
sequence of steps that are specified in your workflow without running
into conflicts.

```bash
workflow --export          # prints out sequence of shell commands
```

**more info.** For more details about these and other options, see
  `workflow --help`.

### design goals

This package takes inspiration from a number of
[existing tools](design/prior_art.md) that have similar aims,
particularly [GNU make](http://www.gnu.org/software/make/) that has
[many desirable properties of working with data workflows](http://bost.ocks.org/mike/make/). Specifically,
the design goals for this project are to:

- *Provide an easy-to-use framework.* This applies for n00bs and pros
  alike. Use human-readable syntax.
- *Prevent, as much as reasonably possible, costly mistakes.* Avoid
  inadvertantly rerunning commands that overwrite results or executing
  commands that take a long time.
- *Encourage good development practices, but allow for flexibility.*
  There's a tradeoff here, but we have [an opinion](#op-ed) on how to
  do this in a good way.

Many of these concepts have been captured in the original the roadmap
for [workflow.yaml](design/workflow.yaml) and the
[command line interface](design/command_line_interface.sh) design
specification. Most of these concepts have been implmented or are on
the roadmap, but if you have any suggestions for other ideas, please
[add them](issues)!


### developing

1. Fork and clone the project.

   ```bash
   git clone https://github.com/YOUR-USERNAME/data-workflow.git
   ```

2. Create a virtual environment and install the dependencies with [virtualenvwrapper](http://virtualenvwrapper.readthedocs.org/en/latest/)

   ```bash
   mkvirtualenv data-workflow
   pip install -r REQUIREMENTS -r examples/REQUIREMENTS
   ```

3. Adjust `PYTHONPATH`, `PATH`, and python environment so you can use
   the development version.

   ```bash
   export PYTHONPATH=$PYTHONPATH:`pwd`
   export PATH=$PATH:`pwd`/bin
   workon data-workflow
   ```

4. Make sure everything is working by executing workflows in
   `examples/*/workflow.yaml`

   ```bash
   cd examples/reuters-tfidf
   workflow
   ```

5. Contribute! There are several [open issues](issues) that provide
   good places to dig in.
