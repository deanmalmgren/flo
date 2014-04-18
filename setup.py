import glob
import os
from setuptools import setup

import flo

# get all of the scripts
scripts = glob.glob("bin/*")

# read in the description from README
with open("README.md") as stream:
    long_description = stream.read()

github_url='https://github.com/deanmalmgren/flo'

# read in the dependencies from the virtualenv requirements file
dependencies = []
filename = "REQUIREMENTS"
with open(filename, 'r') as stream:
    for line in stream:
        package = line.strip().split('#')[0]
        if package:
            dependencies.append(package)

setup(
    name=flo.__name__,
    version=flo.VERSION,
    description="enable rapid iteration and development of data workflows",
    long_description=long_description,
    url=github_url,
    download_url="%s/archives/master" % github_url,
    author='Dean Malmgren',
    author_email='dean.malmgren@datascopeanalytics.com',
    license='MIT',
    scripts=scripts,
    packages=[
        'flo',
        'flo.commands',
        'flo.resources',
        'flo.tasks',
    ],
    install_requires=dependencies,
    zip_safe=False,
)
