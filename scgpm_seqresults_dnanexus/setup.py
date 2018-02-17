
# For some usefule documentation, see
# https://docs.python.org/2/distutils/setupscript.html.
# This page is useful for dependencies: 
# http://python-packaging.readthedocs.io/en/latest/dependencies.html.

from distutils.core import setup

setup(
  name = "scgpm_seqresults_dnanexus",
  version = "0.1.0",
  description = "Utilities for working with the SCGPM Sequencing Center application logic on DNAnexus.",
  author = "Nathaniel Watson",
  author_email = "nathankw@stanford.edu",
  url = "https://github.com/StanfordBioinformatics/scgpm_seqresults_dnanexus.git",
  packages = [
    "https://github.com/StanfordBioinformatics/gbsc_dnanexus.git",
    "https://github.com/StanfordBioinformatics/scgpm_lims.git"
  ],
  install_requires = [],
  scripts = ["scgpm_seqresults_dnanexus/scripts/*.py"],
)
