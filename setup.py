
# For some usefule documentation, see
# https://docs.python.org/2/distutils/setupscript.html.
# This page is useful for dependencies: 
# http://python-packaging.readthedocs.io/en/latest/dependencies.html.

from distutils.core import setup
from setuptools import find_packages 
from pip.req import parse_requirements
import glob
import uuid

scripts = glob.glob("scgpm_seqresults_dnanexus/scripts/*.py")
#Remove __init__.py
[scripts.remove(x) for x in scripts if x.endswith("__init__.py")] 

setup(
  name = "scgpm_seqresults_dnanexus",
  version = "0.1.0",
  description = "Utilities for working with the SCGPM Sequencing Center application logic on DNAnexus.",
  author = "Nathaniel Watson",
  author_email = "nathankw@stanford.edu",
  url = "https://github.com/StanfordBioinformatics/scgpm_seqresults_dnanexus.git",
  packages = find_packages(),
  scripts = scripts
)
