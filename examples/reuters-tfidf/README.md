The goal of this example is to show a relatively real-world case of
downloading a data set and running some preliminary analysis on that
data (*e.g.*,
[tf-idf](http://en.wikipedia.org/wiki/Tf%E2%80%93idf)). This was the
first example that was written as a proof of concept that `flo` makes
it possible to quickly throw together data workflows that can be
compelling and useful in very short order --- this was written from
scratch in less than an hour.

Notice that by using `flo`, you end up having some very general
scripts that, in principal, could be reused in other projects. Since
things like `src/normalize_and_stem.py` and `src/calculate_tfidf.py`
have been extracted from the specific context of the data (the
[Reuters corpus](http://www.daviddlewis.com/resources/testcollections/reuters21578/),
in this example), `flo` enables development that creates nice building
blocks for future projects. Of course, these "general purpose" scripts
might expand, be refactored or change altogether, but by
[making it possible for users to write small but compelling scripts](../../#op-ed),
it becomes that much easier to reuse this code in the future.
