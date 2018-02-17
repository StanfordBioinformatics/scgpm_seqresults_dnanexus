# seqcenter_dnanexus

### Utilities for working with the SCGPM Sequencing Center application logic on DNAnexus

This requires the following two packages from GitHub (show with installation command):

pip3 install https://github.com/StanfordBioinformatics/scgpm_lims/archive/master.zip                   
pip3 install https://github.com/nathankw/gbsc_dnanexus/archive/master.zip  

These dependencies unfortunately can't be placed into the setup.py script used by Python's 
Distutils since support for non-PyPI packages is essentially none. Thus, you'll want to install
these two dependencies first before using this package.
