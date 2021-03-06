#!/usr/bin/env python

# Copyright (c) 2015 Fabrice Laporte - kray.me
# The MIT License http://www.opensource.org/licenses/mit-license.php

import os
import sys
import subprocess
import re

from setuptools import setup


def yield_sphinx_only_markup(lines):
    """http://stackoverflow.com/a/25900928/5181
       Cleans-up Sphinx-only constructs (ie from README.rst),
       so that *PyPi* can format it properly.
       type `python setup.py --long-description` to generate the text
    """
    substs = [
        # Selected Sphinx-only Roles.
        (r':abbr:`([^`]+)`', r'\1'),
        (r':ref:`([^`]+)`', r'`\1`_'),
        (r':term:`([^`]+)`', r'**\1**'),
        (r':dfn:`([^`]+)`', r'**\1**'),
        (r':(samp|guilabel|menuselection):`([^`]+)`', r'``\2``'),

        # Sphinx-only roles:
        (r':(\w+):`([^`]*)`', r'\1(``\2``)'),

        # Sphinx-only Directives.
        (r'\.\. doctest', r'code-block'),
        (r'\.\. plot::', r'.. '),
        (r'\.\. seealso', r'info'),
        (r'\.\. glossary', r'rubric'),
        (r'\.\. figure::', r'.. '),

        # Other
        (r'\|version\|', r'x.x.x'),
    ]

    regex_subs = [(re.compile(regex, re.IGNORECASE), sub)
                  for (regex, sub) in substs]

    def clean_line(line):
        try:
            for (regex, sub) in regex_subs:
                line = regex.sub(sub, line)
        except Exception as ex:
            print("ERROR: %s, (line(%s)" % (regex, sub))
            raise ex

        return line

    for line in lines:
        yield clean_line(line)


def publish():
    """Publish to PyPi"""
    os.system("python setup.py sdist upload")


# Fetch version from git tags, and write to version.py.
# Also, when git is not available (PyPi package), use stored version.py.
version_py = os.path.join(os.path.dirname(__file__), 'version.py')

try:
    version_git = subprocess.check_output(['git', 'describe', '--tags'])[1:-1]
except:
    with open(version_py, 'r') as fh:
        version_git = open(version_py).read().strip().split(
            '=')[-1].replace('"', '')

version_msg = "# Do not edit this file, content generated from git tag"
with open(version_py, 'w') as fh:
    fh.write(version_msg + os.linesep + "__version__=" + version_git)


if sys.argv[-1] == "publish":
    publish()
    sys.exit()

readme_lines = open('README.rst').readlines()
setup(name='qifqif',
      version="{ver}".format(ver=version_git),
      description='QIF file editing tool',
      long_description=''.join(yield_sphinx_only_markup(readme_lines)),
      author='Fabrice Laporte',
      author_email='kraymer@gmail.com',
      url='https://github.com/KraYmer/qifqif',
      license='MIT',
      platforms='ALL',

      packages=[
        'qifqif',
      ],

      entry_points={
        'console_scripts': [
            'qifqif = qifqif:main',
        ],
      },

      install_requires=[
          'blessed',
      ],

      classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Environment :: Console',
        'Topic :: Office/Business :: Financial :: Accounting'
      ])
