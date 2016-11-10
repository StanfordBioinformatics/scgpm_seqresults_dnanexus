#!/usr/bin/env python

###
#Nathaniel Watson
#nathankw@stnford.edu
###

import os
import subprocess
import logging
from argparse import ArgumentParser
import dxpy
import pdb
import re
import sys

import scgpm_seqresults_dnanexus.dnanexus_utils
import encode.dcc_submit as en #module load gbsc/encode/prod
import gbsc_dnanexus #load the environment module gbsc/gbsc_dnanexus
DX_LOGIN_CONF = gbsc_dnanexus.CONF_FILE 

f_formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:   %(message)s')
#create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
#create console handler 
ch = logging.StreamHandler(stream=sys.stdout)
ch.setLevel(logging.DEBUG)
ch.setFormatter(f_formatter)
logger.addHandler(ch)
#posted IDs will get writtin to a file logger
file_log_handler  = logging.FileHandler(filename="2016-07-29_download_log.txt",mode="a")
file_log_handler.setLevel(logging.DEBUG)
file_log_handler.setFormatter(f_formatter)
logger.addHandler(file_log_handler)


description = ""
parser = ArgumentParser(description=description)

parser.add_argument('-u',"--user-name",required=True,help="The login name of the DNAnexus user, who has at least VIEW access to the DNAnexus project containing the FASTQs of interest. An API token must have already been generated for this user and that token must have been added to the DNAnexus login configuration file located at {DX_LOGIN_CONF}.".format(DX_LOGIN_CONF=DX_LOGIN_CONF))
parser.add_argument('-l',"--library-name",required=True,help="The library name of the sample that was sequenced. This is name of the library that was submitted to SCGPM for sequencing. This is added as a property to all sequencing result projects through the 'library_name' project property.")
parser.add_argument("--uhts-run-name",help="The name of the sequencing run in UHTS. This is added as a property to all projects in DNAnexus through the 'seq_run_name' project property. Use this option in combination with --library-name and --lane to further restrict the search space, which is useful especially since multiple DNAnexus projects can have the same library_name property value (i.e. if resequencing the same library).") 
parser.add_argument("--lane",type=int,help="The lane number of the flowcell on which the library was sequenced. This is added as a property to all projects in DNAnexus through the 'seq_lane_index' property. Use this in conjunction with --library-name and --uhts-run-name to further restrict the project search space.")
parser.add_argument('-b',"--barcode",help="The barcode of the sequenced sample. If specified, then only FASTQs with this barcode will be downloaded. Otherwise, all FASTQs will be downloaded.")
parser.add_argument("-d","--file-download-dir",required=True,help="Local directory in which to download the FASTQ files.")
parser.add_argument("--not-found-error",action="store_true",help="Presence of this options means to raise an Exception if a project can't be found on DNAnexus with the provided input.")

args = parser.parse_args()
dx_username = args.user_name
library_name = args.library_name
uhts_run_name = args.uhts_run_name
lane = args.lane
barcode = args.barcode
file_download_dir = args.file_download_dir
if not os.path.exists(file_download_dir):
	os.makedirs(file_download_dir)
not_found_error = args.not_found_error

dxsr = scgpm_seqresults_dnanexus.dnanexus_utils.DxSeqResults(dx_username=dx_username,library_name=library_name,uhts_run_name=uhts_run_name,sequencing_lane=lane)
if dxsr.dx_project_id:
	fastq_dico = dxsr.download_fastqs(barcode=barcode,dest_dir=file_download_dir)
else:
	if not_found_error:
		msg = "Could not find DNAnexus project with library name {library_name}".format(library_name=library_name)
		if barcode:
			msg += " and barcode {barcode}.".format(barcode=barcode)
		else:
			msg += "."
		raise Exception(msg)
		
#fastq_dico: Keys are the file names of the FASTQs and values are the fully qualified paths to the FASTQs.
