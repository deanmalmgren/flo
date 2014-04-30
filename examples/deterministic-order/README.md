The purpose of this example is to illustrate (and test) how the task
graph is always traversed in a predictable order. Namely, tasks are
executed in graph-dependent order. In the event of a tie (in this
example, all of `data/a`'s dependencies), the tasks are executed in
the same order that they appear in the configuration file.
