### general requirements

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


### nice to haves

- [ ] enable continuous iteration through analysis? should this tool deal
  with cyclical workflows? maybe with a `--{loop,cycle}` command line
  argument or something? maybe make it possible to trigger parts of
  the analysis somehow?

- [ ] ability to enable multi-machine workflows?

### example use cases

1. *serial execution.* download a file, run a few sequential steps of
   analysis (e.g., parse, stem, tfidf calculation)

2. *branching execution.* run a simulation, process the results, and
   create 4 separate figures from the results

3. *merging execution + cloud storage.* download data from twitter,
   run some analysis. download some data from facebook, run some
   analysis. merge the results and plot 4 separate figures. store the
   results in S3

4. *serial execution + database storage.* run a simulation, process
   the results, and store some of it in a MySQL database for display
   in a separately maintained web interface

5. *parallel execution.* download 10mm images from flickr, extract the
   RGB spectrum from each, alter the RGB values, and create new images.
