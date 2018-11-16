#!/usr/bin/env python3
# -*- coding: utf-8 -*-

###
# © 2018 The Board of Trustees of the Leland Stanford Junior University
# Nathaniel Watson
# nathankw@stanford.edu
###

import argparse
import sys
import pdb

import dxpy

BARCODE_FIELD_NAME = "barcode"
DX_PROJ_FIELD_NAME = "dx_project_id"
FASTQ_FOLDER_PATH = "/stage0_bcl2fastq/fastqs"

description = """
Adds properties to FASTQ files in DNAnexus. Make sure you are logged into DNAnexus with the appropriate account before using this script in order to ensure access to the relevant projects. Accepts a tab-delimited input file containing properties to add to barcoded FASTQ files, and there must be a header line containing the two fields '{DX_PROJ_FIELD_NAME}' and '{BARCODE_FIELD_NAME}'. The remaining columns will be treated as property names. It is assumed that the directory containing the FASTQ files in each project is named {FASTQ_FOLDER_PATH}.
Note that there are some standard property fields in use. For example, in the CIRM stem-cell project, the following property names are in use:

1) lab_patient_id (i.e. some identifier for a give patient/sample)
2) lab_patient_group (i.e. A categorization for the patient)
3) lab_patient_condition (i.e. a treatment condition, perhaps a medicine and dosage)

The properties that represent FASTQ metadata for some lab protocol/setup should start with 'lab'
followed by an underscore.
""".format(DX_PROJ_FIELD_NAME=DX_PROJ_FIELD_NAME,BARCODE_FIELD_NAME=BARCODE_FIELD_NAME,FASTQ_FOLDER_PATH=FASTQ_FOLDER_PATH)

def get_parser():
  parser = argparse.ArgumentParser(description=description,formatter_class=argparse.RawTextHelpFormatter)
  parser.add_argument("-i","--infile",required=True,help="Tab-delimited input file.")
  return parser

def main():
  parser = get_parser()
  args = parser.parse_args()
  infile = args.infile
  
  PATIENT_ID_PROP_NAME = "lab_patient_id"
  PATIENT_GROUP_PROP_NAME = "lab_patient_group"
  PATIENT_CONDITION_PROP_NAME = "lab_patient_condition"
  
  fh = open(infile)
  #read past header
  header = fh.readline().strip("\n").split("\t")
  try:
    bc_field_index = header.index(BARCODE_FIELD_NAME)
  except ValueError:
    print("Error: Header field '{BARCODE_FIELD_NAME}' missing.".format(BARCODE_FIELD_NAME=BARCODE_FIELD_NAME))
    raise
  try:
    dx_proj_field_index = header.index(DX_PROJ_FIELD_NAME)
  except ValueError:
    print("Error: Header field '{DX_PROJ_FIELD_NAME}' missing.".format(DX_PROJ_FIELD_NAME=DX_PROJ_FIELD_NAME))
    raise
  
  prop_field_indices = []
  for field in header:
    index = header.index(field)
    if index in (bc_field_index,dx_proj_field_index):
      continue
    prop_field_indices.append(index)
  
  line_count = 0
  for line in fh:
    line_count += 1
    line = line.strip("\n")
    if not line:
      continue
    line = line.split("\t")
  
    dx_proj_id = line[dx_proj_field_index].strip()
    if not dx_proj_id:
      raise Exception("Error: DNAnexus Project ID missing in line {cnt}.".format(cnt=line_count))
  
    bc = line[bc_field_index].strip()
    if not bc:
      raise Exception("Error: Barcode missing in line {cnt}.".format(cnt=line_count))
  
    for p in prop_field_indices:
      prop_name = header[p].strip()
      prop_val = line[p].strip()
      proj = dxpy.DXProject(dx_proj_id)
      barcode_glob = "*_{barcode}_*".format(barcode=bc)
      fastqs = list(dxpy.find_data_objects(project=dx_proj_id,folder=FASTQ_FOLDER_PATH,name=barcode_glob,name_mode="glob"))
      #each element in fastqs is a dict of the form {u'project': u'project-F0bv6b00k49KxZvfGQG3v3qQ', u'id': u'file-F0bkxbj02f29xYf3q4BvPYJf'}.
      if len(fastqs) != 2:
        raise Exception("Failed to find two FASTQ files for barcode {barcode} in project {project}.".format(barcode=barcode,project=project))
      for f in fastqs:
        props = dxpy.api.file_describe(object_id=f["id"], input_params={"fields": {"properties": True}})["properties"]
        #note - can also use the get_properties() method of a DXFile object.
        if prop_name not in props:
          props[prop_name] = prop_val
        dxpy.api.file_set_properties(object_id=f["id"],input_params={"project": f["project"],"properties": props})
        print("Updated properties for file {file_id} in project {project}.".format(file_id=f["id"],project=dx_proj_id))

if __name__ == "__main__":
  main()
