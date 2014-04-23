The goal of this example is to show how data workflows need not be
linear, but can be inherently "branchy" with lots of odds and ends of
analysis that are generated along the way. This example also
illustrates how to use [global variables](#templating-variables) in
the `flo.yaml` to specify variables that are used in lots of different
data analysis tasks along the way.

Like with the [reuters-tfidf example](../reuters-tfidf), `flo` tends
to leave users with some very general scripts that could be reused in
other projects. Since things like `src/correlation.py` and
`src/cdf.py` have been extracted from the specific context of the
data, `flo` enables development that creates nice building blocks for
future projects.
