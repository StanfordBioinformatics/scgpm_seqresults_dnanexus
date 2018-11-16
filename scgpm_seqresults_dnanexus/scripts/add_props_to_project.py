#!/usr/bin/env python3
# -*- coding: utf-8 -*-

###
# © 2018 The Board of Trustees of the Leland Stanford Junior University
# Nathaniel Watson
# nathankw@stanford.edu
# 2016-11-18

"""
Given a DNAnexus project ID, or a file containing multiple DNAnexus project IDs (one per line), 
adds one or more properties to each project. Properties are specified as positional key=value arguments.
"""

import argparse

import dxpy

def get_parser():
  parser = argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawTextHelpFormatter)
  group = parser.add_mutually_exclusive_group(required=True)
  group.add_argument("--dx-project-id",help="The DNAnexus project ID to add properties too.")
  group.add_argument("--infile",help="""
    File of DNAnexus project IDs, one per line. Empty lines and lines starting with '#' will be skipped.""")

  parser.add_argument("props",nargs='+',help="""One or more key=value positional arguments, each 
    representing a property key and value pair.""")
  return parser

def main():
  parser = get_parser()
  args = parser.parse_args()
  props = args.props
  dx_proj_id = args.dx_project_id
  infile = args.infile
  
  dx_project_ids = []
  if infile:
    fh = open(infile)
    for line in fh:
      line = line.strip()
      if not line or line.startswith("#"):
        continue
      dx_project_ids.append(line)
    fh.close()
  else:
    dx_project_ids.append(dx_proj_id)
  
  for dx_proj_id in dx_project_ids:
    merge_props = {}
    for p in props:
      if "=" not in p:
        raise Exception("Positional arguments must be specified in key=value format.")
      key,val = p.split("=")
      merge_props[key] = val
  
    dx_proj = dxpy.DXProject(dx_proj_id)
    dx_proj_name = dx_proj.name
  
    dx_properties = dx_proj.describe(input_params={"properties": True})["properties"]
  
    dx_properties.update(merge_props)
    dxpy.api.project_set_properties(object_id=dx_proj_id,input_params={"properties": dx_properties})
  
    print("Updated {proj_id} ({proj_name})".format(proj_id=dx_proj_id,proj_name=dx_proj_name))
  
if __name__ == "__main__":
  main()
