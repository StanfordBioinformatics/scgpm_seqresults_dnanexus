
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

packages = find_packages()
gbsc_dnanexus_packages = find_packages(where="gbsc_dnanexus")
scgpm_lims_packages = find_packages(where="scgpm_lims")
packages.extend(gbsc_dnanexus_packages)
packages.extend(scgpm_lims_packages)

setup(
  name = "scgpm_seqresults_dnanexus",
  version = "0.1.0",
  license = "MIT",
  description = "Utilities for working with the SCGPM Sequencing Center application logic on DNAnexus.",
  author = "Nathaniel Watson",
  author_email = "nathankw@stanford.edu",
  url = "https://github.com/StanfordBioinformatics/scgpm_seqresults_dnanexus.git",
  packages = packages,
  package_dir = {
    "scgpm_lims": "scgpm_lims/scgpm_lims",
    "gbsc_dnanexus": "gbsc_dnanexus/gbsc_dnanexus"
  },
  scripts = scripts
)
