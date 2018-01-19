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
#import encode.dcc_submit as en #module load gbsc/encode/prod
import gbsc_dnanexus #load the environment module gbsc/gbsc_dnanexus

description = ""
parser = ArgumentParser(description=description)

parser.add_argument("--errlog",required=True,help="Log file name to write errors to (i.e. When a DNAnexus project isn't found). Will be opended in append mode.")
parser.add_argument('-l',"--library-name",help="The library name of the sample that was sequenced. This is name of the library that was submitted to SCGPM for sequencing. This is added as a property to all sequencing result projects through the 'library_name' project property.")
parser.add_argument("--uhts-run-name",help="The name of the sequencing run in UHTS. This is added as a property to all projects in DNAnexus through the 'seq_run_name' project property. Use this option in combination with --library-name and --lane to further restrict the search space, which is useful especially since multiple DNAnexus projects can have the same library_name property value (i.e. if resequencing the same library).") 
parser.add_argument("--dx-project-name",help="The name of the sequencing run project in DNAnexus.")
parser.add_argument("--lane",type=int,help="The lane number of the flowcell on which the library was sequenced. This is added as a property to all projects in DNAnexus through the 'seq_lane_index' property. Use this in conjunction with --library-name and --uhts-run-name to further restrict the project search space.")
parser.add_argument('-b',"--barcode",nargs="+",help="The barcode of the sequenced sample. If specified, then only FASTQs with these barcodes will be downloaded. Otherwise, all FASTQs will be downloaded.")
parser.add_argument("-d","--file-download-dir",required=True,help="Local directory in which to download the FASTQ files.")
parser.add_argument("--not-found-error",action="store_true",help="Presence of this options means to raise an Exception if a project can't be found on DNAnexus with the provided input.")

args = parser.parse_args()
library_name = args.library_name
uhts_run_name = args.uhts_run_name
dx_project_name = args.dx_project_name
lane = args.lane
barcodes = args.barcode
file_download_dir = args.file_download_dir
if not os.path.exists(file_download_dir):
	os.makedirs(file_download_dir)
not_found_error = args.not_found_error

#LOGGING
f_formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:   %(message)s')
##create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
##posted IDs will get writtin to a file logger
file_log_handler  = logging.FileHandler(filename=args.errlog,mode="a")
file_log_handler.setLevel(logging.DEBUG)
file_log_handler.setFormatter(f_formatter)
logger.addHandler(file_log_handler)

dxsr = scgpm_seqresults_dnanexus.dnanexus_utils.DxSeqResults(library_name=library_name,uhts_run_name=uhts_run_name,dx_project_name=dx_project_name,sequencing_lane=lane)
if dxsr.dx_project_id:
	for b in barcodes:
		dxsr.download_fastqs(barcode=b,dest_dir=file_download_dir)
else:
	log_msg = """Could not find DNAnexus project for input of:
	DNAnexus User Name   : {user}
	Library Name         : {lib}
	UHTS Run Name:       : {uhts}
	DNAnexus Project Name: {p}
	Sequencing Lane      : {lane}
					 \n""".format(user=scgpm_seqresults_dnanexus.dnanexus_utils.get_dx_username(strip_prefix=True),lib=library_name,uhts=uhts_run_name,p=dx_project_name,lane=lane)
	logger.critical(log_msg)
						
	if not_found_error:
		msg = "Could not find DNAnexus project."
		raise scgpm_seqresults_dnanexus.dnanexus_utils.DxProjectNotFound(msg)
		
#fastq_dico: Keys are the file names of the FASTQs and values are the fully qualified paths to the FASTQs.
