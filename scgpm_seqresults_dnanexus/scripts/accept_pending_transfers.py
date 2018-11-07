#!/usr/bin/env python3
# -*- coding: utf-8 -*-

###
# © 2018 The Board of Trustees of the Leland Stanford Junior University
# Nathaniel Watson
# nathankw@stanford.edu
#August 17, 2016
###

"""
Given all pending DNAnexus project transfers for the user, allows the user to accept transfers 
under a specified billing account, but not just any project. Only projects that have the specified
queue (set in the queue property of the project) will be transferred to the user.
"""

import os
import sys
import argparse
import subprocess

import dxpy

import gbsc_dnanexus.utils #module load gbsc/gbsc_dnanexus
import scgpm_seqresults_dnanexus.dnanexus_utils #module load gbsc/scgpm_seqresults_dnanexus


#The environment module gbsc/gbsc_dnanexus/current should also be loaded in order to log into DNAnexus

def get_parser():
  parser = argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawTextHelpFormatter)
  parser.add_argument('--access-level',required=True,choices=["VIEW","UPLOAD","CONTRIBUTE","ADMINISTER"],help="""
    Permissions level the new member should have on transferred projects.""")

  parser.add_argument('-q',"--queue",required=True,help="""
    The value of the queue property on a DNAnexus project. Only projects that are pending transfer 
    that have this value for the queue property will be transferred to the specified org.""")

  parser.add_argument('-o',"--org",required=True,help="""
    The name of the DNAnexus org under which to accept the project transfers for projects that 
    have their queue property set to the value of the 'queue' argument.""")

  parser.add_argument("--share-with-org",choices=["VIEW","UPLOAD","CONTRIBUTE","ADMINISTER"],help="""
    Add this argument if you'd like to share the transferred projects with the org so that all 
    users of the org will have access to the project. The value you supply should be the access 
    level that members of the org will have.""")
  return parser

def main():
  parser = get_parser()
  args = parser.parse_args()
  org = gbsc_dnanexus.utils.add_dx_orgprefix(args.org)
  
  access_level = args.access_level
  share_with_org = args.share_with_org
  
  queue = args.queue
  
  dx_user = dxpy.whoami().split("-")[1]
  
  script_dir, script_name = os.path.dirname(__file__), os.path.basename(__file__)
  logfile = os.path.join(script_dir,"log_" + dx_user + "_" + os.path.splitext(script_name)[1] + ".txt")
  
  #accept pending transfers
  transferred = scgpm_seqresults_dnanexus.dnanexus_utils.accept_project_transfers(access_level=access_level,queue=queue,org=org,share_with_org=share_with_org)
  #transferred is a dict containting project names as keys and project IDs as values.
  
if __name__ == "__main__":
  main()
