#!/usr/bin/env python

###
#Nathaniel Watson
#Stanford School of Medicine
#August 17, 2016
#nathankw@stanford.edu
###

import os
import sys
from argparse import ArgumentParser
import subprocess
import logging

import dxpy

import gbsc_dnanexus
import scgpm_seqresults_dnanexus.dnanexus_utils


#The environment module gbsc/gbsc_dnanexus/current should also be loaded in order to log into DNAnexus

DX_LOGIN_CONF = gbsc_dnanexus.CONF_FILE

description = "Given all pending DNAnexus project transfers for the specified user, allows the user to accept transfers under a specified billing account, but not just any project. Only projects that have the specified queue (set in the queue property of the project) will be transferred to the user."
parser = ArgumentParser(description=description)
parser.add_argument('-u',"--user-name",required=True,help="The DNAnexus login user name that is to receive pending transfers. An API token must have already been generated for this user and that token must have been added to the DNAnexus login configuration file located at {DX_LOGIN_CONF}.".format(DX_LOGIN_CONF=DX_LOGIN_CONF))
parser.add_argument('-l','--access-level',required=True,choices=["VIEW","UPLOAD","CONTRIBUTE","ADMINISTER"],help="Permissions level the new member should have on transferred projects.")
parser.add_argument('-q',"--queue",required=True,help="The value of the queue property on a DNAnexus project. Only projects that are pending transfer that have this value for the queue property will be transferred to the specified org.")
parser.add_argument('-o',"--org",required=True,help="The name of the DNAnexus org under which to accept the project transfers for projects that have their queue property set to the value of the 'queue' argument.")

args = parser.parse_args()
org = args.org

user = args.user_name
if user.startswith("user-"):
	user = user.split("user-")[1]

access_level = args.access_level

queue = args.queue




#LOG into DNAnexus (The environment module gbsc/gbsc_dnanexus should also be loaded in order to log into DNAnexus)
gbsc_dnanexus
internal_dx_username = "user-" + user

script_dir,script_name = os.path.dirname(__file__),os.path.basename(__file__)
logfile = os.path.join(script_dir,"log_" + user + "_" + os.path.splitext(script_name)[1] + ".txt")

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:   %(message)s')
fhandler = logging.FileHandler(filename=logfile,mode='a')
fhandler.setLevel(logging.INFO)
fhandler.setFormatter(formatter)
chandler = logging.StreamHandler(sys.stdout)
chandler.setLevel(logging.DEBUG)
chandler.setFormatter(formatter)
logger.addHandler(fhandler)
logger.addHandler(chandler)

#accept pending transfers
transferred = scgpm_seqresults_dnanexus.dnanexus_utils.accept_pending_transfers(dx_username=user,access_level=access_level,queue=queue,org=org)
