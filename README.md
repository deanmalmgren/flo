For now, this is a parking lot of ideas concepts that I think would
make it easier to develop and iterate on data workflows as quickly as
possible. Most of these ideas are presently encapculated in the
[design description](design/design.md), which covers the required
functionality and a brief description of some example use cases.

There appear to be a decent number of
[existing tools](design/prior_art.md), some of which I haven't had the
opportunity to try in earnest. Probably I should do that before
investing too much time reinventing the wheel --- particularly
[drake](https://github.com/Factual/drake).

I thought I'd put this out there in case others have thoughts on what
would make for a good data workflow tool. I'm definitely interested in
putting this together if others are equally unsatisfied with existing
alternatives.

In particular, I think the design of the
[specification file](design/workflow.yaml) and the
[command line interface](design/command_line_interface.sh) is
extremely important and if others have thoughts on how to make things
easier to understand or facilitate development, I'm open to any and
all suggestions at this point.

### Developing

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

4. Execute workflows in `examples/*/workflow.yaml`

```
cd examples/serial
workflow
```
