The goal of this project is to make it easy to quickly *develop* data
workflows. This does not provide any opinion on the individual tools
that you might use to conduct an analysis, but it does provide a
framework for quickly conducting an analysis in a reproducible manner.

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

The `creates` key defines the resource that is created. By default, it
is interpretted as a path to a file (relative paths are interpretted
as relative to the `workflow.yaml` file). You can also specify a
protocol, such as `mysql:database/table` (see yet-to-be-implemented #15),
for non-file based resources.

The `depends` key defines the resource(s) on which this task
depends. It is common for `depends` to specify many things, including
data analysis scripts or other tasks from within the
`workflow.yaml`. Multiple dependencies can be defined in a
[YAML list](http://en.wikipedia.org/wiki/YAML#Lists) like this:

```yaml
depends:
  - path/to/some/script.py
  - another/task/creates/target.txt
```

The `alias` key specifies an alternative name that can be used to
specify this task as a `depends` in other parts of the workflow or on
the command line.

The `command` key defines the command(s) that should be executed to
produce the resource specified by the `creates` key.
Like the `depends` key, multiple steps can be defined in a
[YAML list](http://en.wikipedia.org/wiki/YAML#Lists) like this:

```yaml
command:
  - mkdir -p $(dirname {{creates}})
  - python {{depends}} > {{creates}}
```

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

See `workflow --help` for a full list of options, but here are some
highlights:

option


If any of the resources specified in the `depends` have changed since
the last time the workflow was run, XXXX


The original design specification highlights many features that are on
the roadmap for [workflow.yaml](design/workflow.yaml) and the
[command line interface](design/command_line_interface.sh). If you
have any suggestions for other ideas, please [add them](issues)!


### op-ed

TODO give opinion of how users can most effectively take advantage of
this tool


- [ ] encourage users to write small scripts that accomplish very simple
  analysis tasks, not onerous beasts that have many moving parts. This
  makes analysis pipelines much easier to understand and, at least in
  my experience, usually makes intermediate results reusable and easy
  to spot-check.
  - @stringertheory mentioned the ability to work on "one file at a
    time". Perhaps this package could encourage patterns that make
    that possible, just like how scrapy's pipeline processes one
    document at a time
  - perhaps have an opinion about development patterns to facilitate
    rapid development? make it clear how to do this most effectively
- [ ] @bo-peng: What about being able to deal with test/dev data vs
  production data?

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
