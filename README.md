The goal of this project is to make it easy to quickly *develop* data
workflows. This does not provide any opinion on the individual tools
that you might use to conduct an analysis, but it does provide a
framework for quickly conducting an analysis in a reproducible manner.

### quick start

1. *Install this pacakge.* `pip install data-workflow` XXXX NEED TO GET THIS TO WORK

2. *Write a workflow.yaml.* Create a `workflow.yaml` file in the root
   of your project. `workflow.yaml` can
   [have many features](#workflow-yaml-specification), but the basic
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

TODO

are The basic idea is that you can quickly write dependency chains
by concisely writing commands with
[jinja templating](http://jinja.pocoo.org/)

### command line interface

TODO

### features

This package takes inspiration from a number of
[existing tools](design/prior_art.md) that have similar aims,
particularly [GNU make](http://www.gnu.org/software/make/) that has
[many desirable properties of working with data workflows](http://bost.ocks.org/mike/make/).
The original design specification highlights many features that are on
the roadmap for [workflow.yaml](design/workflow.yaml) and the
[command line interface](design/command_line_interface.sh). If you
have any suggestions for other ideas, please [add them](issues), but
here are some high-level things that we have either implemented or
have in the back of our minds:

- [x] compact notation
  - no repeating of information
  - minimal syntactical bloat
  - minimal required structure to get started
- [ ] easy for n00bs to learn how it works without too much effort
  - [ ] good examples and documentation
  - [x] use language that is easy to read/write for data people (YAML, or
    maybe python is better?)
  - [x] ability to use variables in commands in a readable way. no obscure
    shortcuts
  - [x] provides a single place to manipulate filenames
  - [ ] gives guidance on how to write workflow tasks to enable rapid
    prototyping
- [ ] ability to run sub-analysis easily (e.g., per file w/o entire
  directory). this is kinda the equivalent of writing GNU make 'rules'
- [ ] creates/depends on things that are created that are *not* files,
  like database tables, or a result on hdfs or placed in S3
- [ ] run in parallel whenever possible. its 2014
- [x] *not* timestamp based --- hash based. store some archive of hashes
  in the root of the project
- [x] make it possible to run the equivalent of `make` from a subdirectory
  of a project
- [ ] make it possible to split workflow into several files or keep it in
  one single file to organize the workflow in an intuitive way
- [ ] alert users when job is complete
  - [ ] system notifications
  - [ ] email
  - [ ] twitter
  - [ ] SMS
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

It would also be nice to have things like:

- [ ] enable continuous iteration through analysis? should this tool deal
  with cyclical workflows? maybe with a `--{loop,cycle}` command line
  argument or something? maybe make it possible to trigger parts of
  the analysis somehow?
- [ ] ability to enable multi-machine workflows?

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
   good places to dig in and several [other ideas](#features) that
   haven't been translated into issues yet.
