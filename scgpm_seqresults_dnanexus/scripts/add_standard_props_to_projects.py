#!/usr/bin/env python
# -*- coding: utf-8 -*-

###
# © 2018 The Board of Trustees of the Leland Stanford Junior University
# Nathaniel Watson
# nathankw@stanford.edu
# 2016-11-17
###

"""
To fill in.
"""

import argparse
import re

import dxpy

import scgpm_lims

lane_reg = re.compile("_L(\d)_")

def get_parser():
  parser = argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawTextHelpFormatter)
  parser.add_argument("-b","--billing-account",required=True,help="""
    The name of the DNAnexus billing account that the project belongs to. This will only be used 
    to restrict the search of projects.""")
  return parser

def main():
  parser = get_parser()
  uhts_conn = scgpm_lims.Connection()
  args = parser.parse_args()
  billing_account = args.billing_account
  if not billing_account.startswith("org-"):
    billing_account = "org-" + billing_account
  
  projects = list(dxpy.find_projects(billed_to=billing_account))
  #projects = [{u'permissionSources': [u'user-nathankw'], u'public': False, u'id': u'project-BvxVV1Q092QgFKk9Qv2bKj6Z', u'level': u'ADMINISTER'}]
  for p in projects:
    dx_proj = dxpy.DXProject(p["id"])
    dx_proj_name = dx_proj.name
    if not dx_proj_name.startswith("16"):
      continue #not a sequencing results project
    if dx_proj_name == "160715_HEK-ZNF_Controls":
      continue
    print(dx_proj_name)
    uhts_run_name,lane,rest = lane_reg.split(dx_proj_name)
    runinfo = uhts_conn.getruninfo(run=uhts_run_name)["run_info"]
    laneinfo = runinfo["lanes"][lane]
    merge_props = {}
    merge_props["seq_run_name"] = uhts_run_name
    merge_props["seq_lane_index"] = lane
    merge_props["seq_instrument"] = runinfo["sequencing_instrument"]
    merge_props["paired_end"] = str(runinfo["paired_end"])
    merge_props["sequencer_type"] = runinfo["platform_name"]
    merge_props["lab"] = laneinfo["lab"]
    merge_props["queue"] = laneinfo["queue"]
    merge_props["library_name"] = laneinfo["sample_name"].split()[0] #take first whitespace separated element.
  
    dx_properties = dx_proj.describe(input_params={"properties": True})["properties"]
    #check for empty prop vals and delete them:
    pop_attrs = []
    for dx_prop_name in dx_properties:
      val = dx_properties[dx_prop_name].strip()
      if not val:
        pop_attrs.append(dx_prop_name)
    for pa in pop_attrs:
      dx_properties.pop(pa)
  
    dx_properties.update(merge_props)
    dxpy.api.project_set_properties(object_id=dx_proj.id,input_params={"properties": dx_properties})
  
if __name__ == "__main__":
  main()
