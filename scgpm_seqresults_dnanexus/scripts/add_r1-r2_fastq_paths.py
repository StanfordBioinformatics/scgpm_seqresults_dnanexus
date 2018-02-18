#!/usr/bin/env python
# -*- coding: utf-8 -*-

###
# © 2018 The Board of Trustees of the Leland Stanford Junior University
# Nathaniel Watson
# nathankw@stanford.edu
# 2016-11-17
###

"""
Retrieves the FASTQ file names in DNAnexus for the specified sequenced libraries. The tab-delimited input file may be provided in one of two formats.

Format 1:
  1) DNAnexus project name
  2) barcode

Format 2
  1) uhts run name
  2) lane
  3) barcode,

The format in use is determined by the number of header fields present in the header line, which must appear as the very first line in the input file and begin with a '#'.

The output file is identical to the input file, with the exception of two new columns at the start of the file being the FASTQ file name on the DNAnexus platform, and the read number. Thus, the output columns are:

  1) FASTQ file name
  2) Read number (1 for forward reads, 2 for reverse reads)

followed by the input file columns. Note that at present, one of three warnings may be output to stdout.
The possible warnings are triggered whenver

- A DNAnexus project isn't found based on the provided criteria.
- A DNAnexus project was found, but there were not any FASTQ files found within having the specified barcodes.
- A DNAnexus project was found, but only a forward reads or reverse reads FASTQ file was found, not both.

The last warning thus implies that the script assumes all reads are paired-end, which is true.
"""

import argparse
import os
import sys

import scgpm_seqresults_dnanexus.dnanexus_utils
import gbsc_dnanexus.utils  #gbsc_dnanexus git submodule containing utils Python module that can be used to log into DNAnexus.
import gbsc_dnanexus

def get_parser():
  parser = argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawTextHelpFormatter)
  parser.add_argument("-i","--infile",required=True,help="""
    Tab-delimited input file in one of two formats. In each format, the first line must be a 
    header line starting with a '#'. Empty lines and lines beginning with '#' are ignored. The 
    first format contains only two columns with the 1st containing the DNAnexus project name, and 
    the second the barcode. The second format contains the three columns uhts_run name, lane, and 
    barcode. The number of columns present in the header line determines the format - two fields 
    for the first format, and three fields for the latter. A field-header line starting with
    '#' is required as the first line.""")

  parser.add_argument("-o","--outfile",required=True)
  return parser

def main():
  parser = get_parser()
  args = parser.parse_args()
  infile = args.infile
  
  outfile = args.outfile
  fout = open(outfile,'w')
  fh = open(outfile,"w")
  
  fh = open(infile)
  header = fh.readline().strip()
  if not header.startswith("#"):
    raise Exception("Missing header field-header line starting with '#' as first line in --infile.")
  header = header.split("\t")
  if len(header) == 2:
    FMT = 1
  else:
    FMT = 2
  
  index = 0
  dico = {}
  for line in fh:
    index += 1
    line =  line.strip("\n")
    if not line or line.startswith("#"):
      continue
    dico[index] = {}
    dico[index]["line"] = line
    dico[index]["fastq_files"] = {}
  
  for i in sorted(dico):
    line = dico[i]["line"]
    line = line.split("\t")
    if FMT == 1:
      dx_proj_name = line[0]
      barcode = line[1]
      dxsr = scgpm_seqresults_dnanexus.dnanexus_utils.DxSeqResults(dx_project_name=dx_proj_name)
    else:
      run_name = line[0].strip()
      lane = line[1].strip()
      barcode = line[2].strip()
      dxsr = scgpm_seqresults_dnanexus.dnanexus_utils.DxSeqResults(uhts_run_name=run_name,sequencing_lane=lane)
    if not dxsr.dx_project_id:
      #no project found.
      print("Warning: No DNAnexus project found for line {} in input file.".format(index + 1))
      continue
    try:
      fastq_files_props = dxsr.get_fastq_files_props(barcode=barcode)
      #This is a dict keyed by DXFile objects, each representing a FASTQ file. Each key's value is
      # a dictionary of the file's properties on the DNAnexus platform.
    except scgpm_seqresults_dnanexus.dnanexus_utils.FastqNotFound:
      print("Warning: No FASTQ files found for line {} in input file.".format(index + 1))
      continue
    if len(fastq_files_props) == 1:
      print("Warning: There was only one FASTQ file found for line {} in input file. If this is not paired-end sequencing, you can ignore this warning.".format(index + 1))
    for dxfile in fastq_files_props:
      fastq_props = fastq_files_props[dxfile]
      read_num = int(fastq_props["read"])
      file_name = fastq_props["fastq_file_name"]
      dico[i]["fastq_files"][read_num] = file_name
  
  for i in sorted(dico):
    data = dico[i]
    line = dico[i]["line"]
    if data["fastq_files"]:
      for read_num in sorted(data["fastq_files"]):
        file_name = data["fastq_files"][read_num]
        fout.write("\t".join([file_name,str(read_num),line]) + "\n")
    else:
      fout.write("\t\t" + line + "\n")
    fout.flush()
    os.fsync(fout.fileno())
  
  fout.close()
  
  
if __name__ == "__main__":
  main()
