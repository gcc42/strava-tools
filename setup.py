#!/usr/bin/env python

import os

from setuptools import setup, find_packages
from stravatools import __version__

DESCRIPTION = 'Strava Command-Line Tools'

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

with open(os.path.join(here, 'requirements.txt'), encoding='utf-8') as f:
    requirements = [ x for x in f.read().split('\n') if len(x) > 1 ]

setup(
    python_requires='>=3.5',
    name='strava-tools',
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type='text/markdown',
    version=__version__,
    license='MIT',
    author='Pierrick Terrettaz',
    author_email='pierrick@gmail.com',
    url='https://github.com/terrettaz/strava-tools',
    packages=find_packages(),
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Development Status :: 3 - Alpha",
        "Natural Language :: English",
        "Topic :: Utilities"
    ],
    install_requires=requirements,
    tests_require=["pytest", "requests-mock"],
    entry_points={
        'console_scripts': [
            'strava-shell = stravatools.cli.shell:main'
        ],
    },
)