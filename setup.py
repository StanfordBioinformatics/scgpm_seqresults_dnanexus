
# For some usefule documentation, see
# https://docs.python.org/2/distutils/setupscript.html.
# This page is useful for dependencies:
# http://python-packaging.readthedocs.io/en/latest/dependencies.html.

import glob
from setuptools import setup, find_packages
import uuid

scripts = glob.glob("scgpm_seqresults_dnanexus/scripts/*.py")
#Remove __init__.py
[scripts.remove(x) for x in scripts if x.endswith("__init__.py")]

with open("README.md", "r") as fh:
    long_description = fh.read()

packages = find_packages()
gbsc_dnanexus_packages = find_packages(where="gbsc_dnanexus")
scgpm_lims_packages = find_packages(where="scgpm_lims")
packages.extend(gbsc_dnanexus_packages)
packages.extend(scgpm_lims_packages)

setup(
  author = "Nathaniel Watson",
  author_email = "nathankw@stanford.edu",
  classifiers = [
      "Programming Language :: Python :: 3",
      "License :: OSI Approved :: MIT License",
      "Operating System :: OS Independent",
  ],
  description = "Utilities for working with the SCGPM Sequencing Center application logic on DNAnexus.",
  install_requires = [
      "dxpy",
  ]
  long_description = long_description,
  long_description_content_type = "text/markdown",
  name = "scgpm-seqresults-dnanexus",
  packages = packages,
  package_dir = {
    "scgpm_lims": "scgpm_lims/scgpm_lims",
    "gbsc_dnanexus": "gbsc_dnanexus/gbsc_dnanexus"
  },
  project_urls = {
      "Read the Docs": "https://scgpm-seqresults-dnanexus.readthedocs.io/en/latest",
  },
  scripts = scripts,
  url = "https://github.com/StanfordBioinformatics/scgpm_seqresults_dnanexus.git",
  version = "0.1.0",
)
