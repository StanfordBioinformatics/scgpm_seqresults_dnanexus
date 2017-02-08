#!/usr/bin/env python

###
#Nathaniel Watson
#nathankw@stnford.edu
###

import os
import subprocess
import logging
from argparse import ArgumentParser
import sys

import scgpm_seqresults_dnanexus.dnanexus_utils
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
#file_log_handler  = logging.FileHandler(filename="2016-07-29_download_log.txt",mode="a")
#file_log_handler.setLevel(logging.DEBUG)
#file_log_handler.setFormatter(f_formatter)
#logger.addHandler(file_log_handler)


description = "Calls download_fastqs.py in batch, provided an input file specifying the FASTQs to download."
parser = ArgumentParser(description=description)

parser.add_argument('-i',"--infile",required=True,help="The tab-delimited input file with the following fields: 1) uhts run name, 2) library name, and 3) barcode. Empty lines and lines beginning with a '#' will be skipped. There isn't a header line.")
parser.add_argument('-u',"--user-name",required=True,help="The login name of the DNAnexus user, who has at least VIEW access to the DNAnexus project containing the FASTQs of interest. An API token must have already been generated for this user and that token must have been added to the DNAnexus login configuration file located at {DX_LOGIN_CONF}.".format(DX_LOGIN_CONF=DX_LOGIN_CONF))
parser.add_argument("-d","--file-download-dir",required=True,help="Local directory in which to download the FASTQ files.")
parser.add_argument("--not-found-error",action="store_true",help="Presence of this options means to raise an Exception if a project can't be found on DNAnexus with the provided input.")

args = parser.parse_args()
infile = args.infile
dx_user_name = args.user_name
file_download_dir = args.file_download_dir
if not os.path.exists(file_download_dir):
	os.makedirs(file_download_dir)
not_found_error = args.not_found_error

inputs = []
fh = open(infile)
for line in fh:
	line = line.strip("\n")
	if not line:
		continue
	if line.startswith("#"):
		continue
	input_dict = {}
	line = line.split("\t")
	uhts_run_name = line[0].strip()
	library_name = line[1].strip()	
	barcode = line[2].strip()
	input_dict["uhts_run_name"] = uhts_run_name
	input_dict["library_name"] = library_name
	input_dict["barcode"] = barcode
	inputs.append(input_dict)

for i in inputs:
	logger.debug("Fetching FASTQs for " + str(i))
	run_name = i["uhts_run_name"]
	lib_name = i["library_name"]
	barcode = i["barcode"]	
	cmd = "download_fastqs.py --not-found-error -d {file_download_dir} -u {dx_user_name} --uhts-run-name {run_name}  -l {lib_name} -b {barcode}".format(file_download_dir=file_download_dir,dx_user_name=dx_user_name,run_name=run_name,lib_name=lib_name,barcode=barcode) 
	subprocess.check_call(cmd,shell=True)
		
#fastq_dico: Keys are the file names of the FASTQs and values are the fully qualified paths to the FASTQs.
