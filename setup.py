import glob
import os
from setuptools import setup

import workflow

# get all of the scripts
scripts = glob.glob("bin/*")

# read in the description from README
with open("README.md") as stream:
    long_description = stream.read()

github_url='https://github.com/deanmalmgren/data-workflow'

# read in the dependencies from the virtualenv requirements file
dependencies = []
filename = "REQUIREMENTS"
with open(filename, 'r') as stream:
    for line in stream:
        package = line.strip().split('#')[0]
        if package:
            dependencies.append(package)

setup(
    name=workflow.__name__,
    version=workflow.VERSION,
    description="enable rapid iteration and development of data workflows",
    long_description=long_description,
    url=github_url,
    download_url="%s/archives/master" % github_url,
    author='Dean Malmgren',
    author_email='dean.malmgren@datascopeanalytics.com',
    license='MIT',
    scripts=scripts,
    packages=[
        'workflow',
        'workflow.resources',
        'workflow.commands',
    ],
    install_requires=dependencies,
    zip_safe=False,
)
