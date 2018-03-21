#!/usr/bin/env python3
# -*- coding: utf-8 -*-

###
# © 2018 The Board of Trustees of the Leland Stanford Junior University
# Nathaniel Watson
# nathankw@stanford.edu
# 2016-10-09
###

"""
Downloads all projects from DNanexus that have the given value for the 'seq_run_name' property set. A billing account can be specified in order to limit the project search space to only those belonging to that account.
"""

import subprocess
import argparse

import dxpy

import gbsc_dnanexus.utils
import scgpm_seqresults_dnanexus.dnanexus_utils as u

def get_parser():
  parser = argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawTextHelpFormatter)
  parser.add_argument("--seq-run-name",required=True,help="""
    The name of the sequencing run, as set by the 'seq_run_name' property of a DNAnexus project.""")

  parser.add_argument("--download-dir",required=True,help="""
    Local directory in which to download the DNAnexus project.""")

  parser.add_argument('-b',"--billing-account-id",help="""
    A DNAnexus user account or org to restrict the project search in DNAnexus.""")

  parser.add_argument('-s',"--skip-projects",nargs="+",help="""
    One ore more DNAnexus project IDs (space delimited) to skip downloading. Useful if you need 
    to download multiple projects that have the same value for the 'seq_run_name' property, but 
    not all if, for example some were already downloaded.""")
  return parser

def main():
  parser = get_parser()
  args = parser.parse_args()
  
  seq_run_name = args.seq_run_name
  skip_projects = args.skip_projects
  download_dir = args.download_dir
  billing_account_id = args.billing_account_id
  if billing_account_id:
    if not billing_account_id.startswith(gbsc_dnanexus.utils.DX_USER_PREFIX) and not billing_account_id.startswith(gbsc_dnanexus.utils.DX_ORG_PREFIX):
      raise Exception("Error - The DNAnexus Billing account, set by the --billing-account argument, must start with with {user} or {org}. Instead, got {value}".format(user=gbsc_dnanexus.utils.DX_USER_PREFIX,org=gbsc_dnanexus.utils.DX_ORG_PREFIX,value=billing_account_id))
  else:
    billing_account_id = None #must be None rather than the empty string in order to work in dxpy.find_projects.
  
  dx_projects = dxpy.find_projects(billed_to=billing_account_id,properties={"seq_run_name":seq_run_name})
  #dx_projects is a generator of dicts of the form:
  #  {u'permissionSources': [u'user-nathankw'], u'public': False, u'id': u'project-BzqVkxj08kVZbPXk54X0P2JY', u'level': u'ADMINISTER'}
  
  popens = []
  for proj in dx_projects:
    proj_id = proj["id"]
    if proj_id in skip_projects:
      continue
    cmd = "download_project.py --dx-project-id {proj_id} --download-dir {download_dir}".format(proj_id=proj_id,download_dir=download_dir)
    print("Running command {cmd}.".format(cmd=cmd))
    popens.append(subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE))
  for p in popens:
    stdout,stderr = p.communicate()
    print(stdout)
    print(stderr)
    print("\n\n")

if __name__ == "__main__":
  main()
