# seqcenter_dnanexus

### Utilities for working with the SCGPM Sequencing Center application logic on DNAnexus

API documentation is on [Read the Docs](https://scgpm-seqresults-dnanexus.readthedocs.io/en/latest/index.html).

Provides high level methods and scripts for working with sequencing results that are stored in DNAnexus projects. This repository is geared towards sequencing result projects that the Stanford Genome Sequencing Center creates in DNAnexus, since there are many project properties that are unique to their workflow that are utilized/queried.  

The heart of this API rests in the **`DxSeqResults()`** class in the **`dnanexus_utils.py`** module. Given a DNAnexus project of interest, a user can use high level methods around that project to do things such as:

* Download QC reports and JSON stats for one or more barcoded samples,
* Download FASTQ files or fetch them as DNAnexus DXFile objects,
* Retrieve the properties that are set on specific FASTQ files,
* and more

There is also a functionality to programatically accept project transfers in DNAnexus. 

The **scripts** are many, and include tools such as:

* Cleaning up projects to save space
* Listing projects and their properties for projects billed to a specific org,
* Downloading fastqs of interest,
* Adding properties to a project
* accepting project transfers

The first point above has been heavily used to save space and costs. The script is called ``scgpm_clean_raw_data.py`` and works by unneccessary extras in the raw_data folder of a project.  It works by running an app on DNAnexus by the same name and cleans out all projects that have been created within the last N days. 


