#!/usr/bin/env python3
# -*- coding: utf-8 -*-

###
# © 2018 The Board of Trustees of the Leland Stanford Junior University
# Nathaniel Watson
# nathankw@stanford.edu
###

"""
Downloads a SCGPM sequencing results project from DNAnexus. Currently, there is one DNAnexus project for each lane of Illumina sequencing. A folder will be created by the name of the DNAnexus project within the specified output folder. The project folder will contain a FASTQ subfolder, a FASTQC subfolder, and several files including 1) the sequencing QC report, 2) the list of barcodes in the sequencing lane in barcodes.json, run information in run_details.json, and a meta-data tarball by the name of ${sequencing_run_name}.metadata.tar. This last file contains important XML files output by the sequencer, such as the runParameters.XML and RunInfo.xml.
"""

import argparse
import sys

import dxpy

import gbsc_dnanexus
import scgpm_seqresults_dnanexus.dnanexus_utils as u

def get_parser():
  parser = argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawTextHelpFormatter)
  parser.add_argument("--download-dir",required=True,help="""
    Local directory in which to download the DNAnexus project.""")
  group = parser.add_mutually_exclusive_group(required=True)
  group.add_argument("--dx-project-id",help="The DNAnexus ID of the project to download.")
  group.add_argument("--dx-project-list",help="""
    File with DNAnexus project IDs, one per line, for batch project download. Empty lines and 
    lines starting with a '#' will be ignored.""")
  return parser

def main():
  parser = args.get_parser()
  args = parser.parse_args()
  
  dx_project_id = args.dx_project_id
  dx_project_list= args.dx_project_list
  download_dir = args.download_dir
  
  dx_project_ids = []
  if dx_project_id:
    dx_project_ids.append(dx_project_id)
  else:
    fh = open(dx_project_list)
    for line in fh:
      line = line.strip("\n")
      if not line:
        continue
      if line.startswith("#"):
        continue
      dx_project_ids.append(line.strip())
    fh.close()
  
  for i in dx_project_ids:
    dxsr = u.DxSeqResults(dx_project_id=dx_project_id)
    dxsr.download_project(download_dir=download_dir)
  
if __name__ == "__main__":
  main() 
