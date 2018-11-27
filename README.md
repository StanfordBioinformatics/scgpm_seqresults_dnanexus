# seqcenter_dnanexus

### Utilities for working with the SCGPM Sequencing Center application logic on DNAnexus

API documentation is on [Read the Docs](https://scgpm-seqresults-dnanexus.readthedocs.io/en/latest/index.html).

Provides high level methods and scripts for working with sequencing results that are stored in DNAnexus projects. This repository is geared towards sequencing result projects that the Stanford Genome Sequencing Center creates in DNAnexus, since there are many project properties that are unique to their workflow which are utilized and queried here.   

The heart of this API rests in the **`DxSeqResults()`** class in the **`dnanexus_utils.py`** module. Given a DNAnexus project of interest, a user can use high level methods around that project to do things such as:

* Download QC reports and JSON stats for one or more barcoded samples,
* Download FASTQ files or fetch them as DNAnexus DXFile objects,
* Retrieve the properties that are set on specific FASTQ files,
* accept project transfers in DNAnexus,
* and more.

The **scripts** are many, and include tools such as:

* Clean up projects to save space,
* List projects and their properties for projects billed to a specific org,
* Download fastqs of interest,
* Add properties to a project,
* Accept project transfers

The first point above has been heavily used to save space and costs. The script is called ``scgpm_clean_raw_data.py`` and works by removing unneccessary extras in the raw_data folder of a project.  It works by running an app on DNAnexus by the same name and cleans out all projects that have been created within the last N days. 


