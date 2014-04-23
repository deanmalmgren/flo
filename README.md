### op-ed

> "It should be easy to swap in production data for development
> data." - @bo-peng

> "It should be easy to work on one file at a time." - @stringertheory

> "It should be easy to avoid making costly mistakes." - @deanmalmgren

There are many ways one could conceivably write a data analysis
workflow from scratch, from writing single programs that ingest,
analyze and visualize data to simple scripts that each handle one part
of the puzzle. Particularly when developing workflows from scratch, we
have the strong opinion that writing small scripts with intermediate
outputs is a much more effective way to develop a prototype data
workflow. In our experience, we find it to be very convenient to edit
a script, run it, and repeat several times to make sure it is behaving
the way we intend. For one thing, this pattern makes it far easier to
spot check results using a litany of available command line tools. For
another, this pattern makes it easy to identify weak links (*e.g.*
incorrect results, poor performance, etc.) in the analysis and improve
them piece by piece after the entire workflow has been written the
first time.

This package is deliberately designed to help users write small, but
compact workflow prototypes using whatever tools they prefer --- R,
pandas, scipy, hadoop. The goal here is not to provide a substitute
for these tools, but rather to be the glue that sticks them together.


### quick start

1. *Install this package.*

   ```bash
   pip install -e git+https://github.com/deanmalmgren/flo#egg=flo
   ```

2. *Write a flo.yaml.* Create a `flo.yaml` file in the root
   of your project. `flo.yaml` can
   [have many features](#floyaml-specification), but the basic
   idea is to make it easy to quickly define a sequence of dependent
   tasks in an easy-to-read way. There are several
   [examples](examples/), the simplest of which is the
   [hello-world example](examples/hello-world/flo.yaml). Briefly,
   every task is a YAML object that has a `creates` key that
   represents the resource that is created by this task and a
   `command` key that defines the command that are required to create
   the resource defined in `creates`. You can optionally define a
   `depends` key that lists resources, either filenames on disk or
   other task `creates` targets, to quickly set up dependency
   chains. You can optionally omit the `command` key to create
   pseudotasks that are collections of other tasks for quickly running
   a subcomponent of the analysis.

3. *Execute your workflow.* From the same directory as the
   `flo.yaml` file (or any child directory), execute `flo run` and
   this will run each task defined in your `flo.yaml` until
   everything is complete. If any task definition in the
   `flo.yaml` or the contents of its dependencies change,
   re-running `flo run` will only redo the parts of the workflow that
   are out of sync since the last time you ran it. The `flo`
   command has
   [several other convenience options](#command-line-interface) to
   facilitate quickly writing data workflows. Running the
   [hello-world example](examples/hello-world) for the first time
   yields something like this:

   ![hello world screenshot](http://i.imgur.com/WZsUJNN.png)

4. *Repeat steps 2-3 until your data workflow is complete.* When
   developing a data workflow, it is common to write an entire
   workflow and then go back and revisit particular parts of the
   analysis. The entire purpose of this package is to make it easy to
   refine task definitions and quickly re-run workflows with
   confidence that the user will not ruin previous results or start a
   simulation that takes a long time.


### flo.yaml specification

Individual analysis tasks are defined as
[YAML objects](http://en.wikipedia.org/wiki/YAML#Associative_arrays)
in `flo.yaml` with something like this:

```yaml
---
creates: path/to/some/output/file.txt
depends: path/to/some/script.py
command: python {{depends}} > {{creates}}
```

Every task YAML object must have a [`creates`](#creates) key and can
optionally contain [`command`](#command) and
[`depends`](#depends) keys. The order of these keys does not matter;
the above order is chosen for explanatory purposes only.

##### creates

The `creates` key defines the resource that is created. By default, it
is interpreted as a path to a file (relative paths are interpreted
as relative to the `flo.yaml` file). You can also specify a
protocol, such as `mysql:database/table` (see yet-to-be-implemented #15),
for non-file based resources.

##### depends

The `depends` key defines the resource(s) on which this task
depends. It is common for `depends` to specify many things, including
data analysis scripts or other tasks from within the
`flo.yaml`. Multiple dependencies can be defined in a
[YAML list](http://en.wikipedia.org/wiki/YAML#Lists) like this:

```yaml
depends:
  - path/to/some/script.py
  - another/task/creates/target.txt
```

##### command

The `command` key defines the command(s) that should be executed to
produce the resource specified by the `creates` key.  Like the
`depends` key, multiple steps can be defined in a
[YAML list](http://en.wikipedia.org/wiki/YAML#Lists) like this:

```yaml
command:
  - mkdir -p $(dirname {{creates}})
  - python {{depends}} > {{creates}}
```

If the `command` key is omitted, this task is treated like a
pseudotask to make it easy to group together a collection of other
tasks like this:

```yaml
creates: figures         # name of pseudotask
depends:
  - path/to/figure/a.png # refers to another task in flo.yaml
  - path/to/figure/b.png # refers to another task in flo.yaml
  - path/to/figure/c.png # refers to another task in flo.yaml
```

##### templating variables

Importantly, the `command` is rendered as a
[jinja template](http://jinja.pocoo.org/) to avoid duplication of
information that is already defined in that task. Its quite common to
use `{{depends}}` and `{{creates}}` in the `command` specification,
but you can also use other variables like this:

```yaml
---
creates: path/to/some/output/file.txt
sigma: 2.137
depends: path/to/some/script.py
command: python {{depends}} {{sigma} > {{creates}}
```

In the aforementioned example, `sigma` is only available when rendering
the jinja template for that task. If you'd like to use `sigma` in
several other tasks, you can alternatively put it in a global
namespace in a flo.yaml like this
([similar example here]("examples/model-correlations")):

```yaml
---
sigma: 2.137
tasks: 
  - 
    creates: path/to/some/output/file.txt
    depends: path/to/some/script.py
    command: python {{depends}} {{sigma} > {{creates}}
  -
    creates: path/to/another/output/file.txt
    depends:
	  - path/to/another/script.py
      - path/to/some/output/file.txt
    command: python {{depends[0]}} {{sigma}} < {{depends[1]}} > {{creates}}
```

Another common use case for global variables is when you have several
tasks that all depend on the same file. You can also use jinja
templating in the `creates` and `depends` attributes of your
`flo.yaml` like this:

```yaml
---
input: data/sp500.html
tasks:
  -
    creates: "{{input}}"
	command:
	  - mkdir -p $(dirname {{creates}})
      - wget http://en.wikipedia.org/wiki/List_of_S%26P_500_companies -O {{creates}}
  -
	creates: data/names.dat
	depends:
      - src/extract_names.py
      - "{{input}}"
	command: python {{depends|join(' ')}} > {{creates}}
  -
	creates: data/symbols.dat
	depends:
      - src/extract_symbols.py
      - "{{input}}"
	command: python {{depends|join(' ')}} > {{creates}}
```

There are several [examples](examples/) for more inspiration on how
you could use the flo.yaml specification. If you have suggestions
for other ideas, please [add them](issues)!


### command line interface

This package ships with the `flo` command, which embodies the
entire command line interface for this package. This command can be
run from the directory that contains `flo.yaml` or any of its
child directories. Output has been formatted to be as useful as
possible, including the task names that are run, the commands that are
run, and how long each task takes. For convenience, this information
is also stored in `.flo/flo.log`. Here, we elaborate on a
few key features of `flo`; see `flo --help` for details
about all available functionality,

##### flo run

By default, the `flo run` command will execute the entire
workflow, or at least the portion of it that is "out of sync" since
the last time it ran. Executing `flo run` twice in a row without
editing any files in the interim will not rerun any steps. If you edit
a particular file in the workflow and re-execute `flo run`, this
will only re-execute the parts that have been affected by the
change. This makes it very easy to iterate quickly on data analysis
problems without having to worry about re-running an arsenal commands
--- you only have to remember one, `flo run`.

```bash
flo run                # runs everything for the first time
flo run                # nothing changed; runs nothing
edit path/to/some/script.py
flo run                # only runs the parts that are affected by change
```

Importantly, if you edit a particular task in the `flo.yaml`
itself, this will cause that particular task to be re-run as well:

```bash
flo run
edit flo.yaml          # change a particular task's command
flo run                # rerun's that command and any dependent task
```

The `flo` command is able to do this by tracking the status of
all `creates`, `depends`, and task definitions by hashing the contents
of these resources. If the contents in any `depends` or the task
itself has changed since the last time that task was run, `flo`
will run that task. For reference, the hashes of all of the `creates`,
`depends`, and workflow task definitions are in `.flo/state.csv`.

##### flo run task_id

Oftentimes we do not want to run the entire workflow, but only a
particular component of it. Like GNU make, you can specify a
particular task by its `creates` value on the
command line like this:

```bash
flo run path/to/some/output/file.txt
```

This limits `flo` to only executing the task defined in
`path/to/some/output/file.txt` and all of its recursive upstream
dependencies.

##### flo run --start-at task_id

Other times we do not want to run the entire workflow, but run
everything after a specific component. We can do that like this:

```bash
flo run --start-at path/to/some/file.txt
```

This limits `flo` to only executing the task defined in
`path/to/some/file.txt` and all of its recursive **downstream**
dependencies. This can be combined with `run task_id` to only all
tasks between two specified tasks like this:

```bash
flo run --start-at path/to/some/file.txt path/to/some/output/file.txt
```

##### flo run --only task_id

If you ever want to only run one task, say a task that creates
`path/to/some/file.txt`, you can specify that task as both the
starting and ending point of the workflow run with `--only`:

```bash
flo run --only path/to/some/file.txt
```

This is analogous to specifying the starting and ending point like this:

```bash
flo run --start-at path/to/some/file.txt path/to/some/file.txt
```

##### flo run --skip task_id

In some situations --- especially with very long-running tasks ---
it is convenient to be able to skip particular tasks like this:

```bash
flo run --skip path/to/some/file.txt
```

This eliminates the task associated with `path/to/some/file.txt` from
the workflow but preserves the dependency chain so that other tasks
are still executed in the proper order.

##### flo run --dry-run

While [we don't recommend it](#op-ed), its not uncommon to get "in the
zone" and make several edits to analysis scripts before re-running
your workflow. Because we're human, its easy to incorrectly remember
the files you edited and how they may affect re-running the
workflow. To help, the `--dry-run` command line option lets you see
which commands will be run and approximately how much time it should
take (!!!).

```bash
flo run
edit path/to/some/script.py
edit path/to/another/script.py
flo run --dry-run     # don't run anything, just report what would be done
```

For reference, `flo` stores the duration of each task in
`.flo/duration.csv`.

##### flo run --force

Sometimes it is convenient to rerun an entire workflow, regardless of
the current status of the files that were generated.

```bash
flo run
# don't do anything for several months
echo "Rip Van Winkle awakens and wonders, where did I leave off again?"
echo "Screw it, lets just redo the entire analysis"
flo run --force
```

##### flo run --notify

For long-running workflows, it is convenient to be alerted when the
entire workflow completes. The `--notify` command line option makes it
possible to have the last 100 lines of the `.flo/flo.log`
sent to an email address specified on the command line.

```bash
flo run --notify j.doe@example.com
```

##### flo clean

Sometimes you want to start with a clean slate. Perhaps the data you
originally started with is dated or you want to be confident a
workflow properly runs from start to finish before inviting
collaborators. Whatever the case, the `flo clean` command can be
useful for removing all `creates` targets that are defined in
`flo.yaml`. With the `--force` command line option, you can
remove all files without having to confirm that you want to remove
them. If you just want to remove a particular target, you can use
`flo clean task_id` to only remove that `creates` target.

```bash
flo clean              # asks user if they want to remove `creates` results
flo clean --force      # removes all `creates` targets without confirmation
flo clean a/task       # only remove the a/task target
```

##### flo archive

Before removing or totally redoing an analysis, I've often found it
useful to backup my results and compare the differences later. The
`flo archive` command makes it easy to quickly backup an entire
flo (including generated `creates` targets, source code specified
in `depends`, and the underlying `flo.yaml`) and compare it to
previous versions.

```bash
flo archive            # store archive in .flo/archives/*.tar.bz2
for i in `seq 20`; do
	edit path/to/some/script.py
	flo run
done
echo 'oh crap, this sequence of changes was a mistake'
flo archive --restore  # uncompresses archive
```

##### autocomplete

Autocompletion of available options with workflow is enabled by
@kislyuk's amazing
[autocomplete](https://github.com/kislyuk/argcomplete) package. Follow
instructions to
[enable global autocomplete](https://github.com/kislyuk/argcomplete#activating-global-completion)
and you should be all set. As an example, this is also configured in
the [virtual machine provisioning](provision/development.sh#L17).


### design goals

This package takes inspiration from a number of
[existing tools](design/prior_art.md) that have similar aims,
particularly [GNU make](http://www.gnu.org/software/make/) that has
[many desirable properties of working with data workflows](http://bost.ocks.org/mike/make/). Specifically,
the design goals for this project are to:

- *Provide an easy-to-use framework.* This applies for n00bs and pros
  alike. Use human-readable syntax.
- *Prevent, as much as reasonably possible, costly mistakes.* Avoid
  inadvertently rerunning commands that overwrite results or executing
  commands that take a long time.
- *Encourage good development practices, but allow for flexibility.*
  There's a tradeoff here, but we have [an opinion](#op-ed) on how to
  do this in a good way.

Many of these concepts have been captured in the original road map
for [flo.yaml](design/flo.yaml) and the
[command line interface](design/command_line_interface.sh) design
specification. Most of these concepts have been implemented or are on
the road map, but if you have any suggestions for other ideas, please
[add them](issues)!


### developing

1. [Fork](https://github.com/deanmalmgren/flo/fork) and
   clone the project.

   ```bash
   git clone https://github.com/YOUR-USERNAME/flo.git
   ```

2. Install [Vagrant](http://vagrantup.com/downloads) and
   [Virtualbox](https://www.virtualbox.org/wiki/Downloads) and launch
   the development virtual machine:

   ```bash
   vagrant up && vagrant provision
   ```

   On `vagrant ssh`ing to the virtual machine, note that the
   `PYTHONPATH` and `PATH` environment variables have been altered in
   this virtual machine so that any changes you make to your local
   data workflow scripts are automatically reloaded.
   
3. On the virtual machine, make sure everything is working by
   executing workflows in `examples/*/flo.yaml`

   ```bash
   cd examples/reuters-tfidf
   flo run
   ```

4. To be more thorough, there is an automated suite of functional
   tests to make sure any patches you have made haven't disturbed the
   behavior of this package in any substantiative way.

   ```bash
   ./tests/run_functional_tests.sh
   ```

   These functional tests are designed to be run on an Ubuntu 12.04
   LTS server, just like the virtual machine and the server that runs
   the travis-ci test suite. There are some other tests that have been
   added along the way in the [Travis configuration](.travis.yml).
   For your convenience, you can run all of these tests with:

   ```bash
   ./tests/run.py
   ```

   Current build status:
   [![Build Status](https://travis-ci.org/deanmalmgren/flo.png)](https://travis-ci.org/deanmalmgren/flo)

5. Contribute! There are several [open issues](issues) that provide
   good places to dig in. Check out the
   [contribution guidelines](CONTRIBUTING.md) and send pull
   requests; your help is greatly appreciated!
