#!/usr/bin/env python

###
#Nathaniel Watson
#nathankw@stnford.edu
###

import os
import time
import subprocess
import logging
import argparse
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

def log_file_name(ext=False):
	""" 
	Function : Creates a logfile name, named after this script and includes the number of seconds since the Epoch. 
	           An optional extension can be specified to make the logfile name more meaningful regarding its purpose. 
	Args     : ext - The extension to add to the log file name to indicate its purpose, i.e. ERR for error messages.
	Returns  : str. 
	"""
	script_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
	val = script_name + "_" + str(int(time.time())) + "_LOG"
	if ext:
	  val += "_" + ext 
	val += ".txt"
	return val 

ERRLOG = log_file_name(ext="ERR")


description = "Calls download_fastqs.py in batch, provided an input file specifying the FASTQs to download."
parser = argparse.ArgumentParser(description=description,formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument('-i',"--infile",required=True,help="""Tab-delimited input file in one of two formats. Empty lines and lines beginning with a '#' will be skipped. The first line must be a header line. The first format is used if you don't know the DNAnexus project. Format 1 has the following fields: 
	1) uhts run name, 
	2) sequencing lane,
	3) library name,
	4) barcode. 
Format 2 has the following fields:
	1) dnanexus_project_name,
	2) barcode
The script will act on format 1 parsing rules if 4 Fields are detected in the header line, and those of the second format if two fields are detected in the header line. Any other number of fields found in the header line will result in an error.

A note on format 1, you don't have to include values for each field. For unknown values, just leave it blank. These values are stored as properties on a DNAnexus project, and the search for a DNAnexus project will be successful if you supply enough property information to uniquely identify a project.
""")
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

fh = open(infile)
header = fh.readline().strip().split("\t") #read past header
length_header = len(header)

inputs = [] #list of dicts.
if length_header not in [2,4]:
	raise Exception("The header line has a number of fields ({}) that is not supported.".format(length_header))

if length_header == 2: 
	line_cnt = 0
	for line in fh:
		line_cnt += 1
		line = line.strip("\n")
		if not line:
			continue
		if line.startswith("#"):
			continue
		line = line.split("\t")
		dx_proj_name = line[0].strip()
		barcode = line[1].strip()
		if not dx_proj_name:
			raise Exception("Value for 'dnanexus_project_name' field needed one line {}.".format(line_cnt))
		if not barcode:
			raise Exception("Value for 'barcode' field needed one line {}.".format(line_cnt))
		inputs.append({"dx_proj_name": dx_proj_name, "barcode": barcode})

	for i in inputs:
		logger.info("Fetching FASTQs for " + str(i))
		dx_proj_name = i["dx_proj_name"]
		barcode = i["barcode"]	
		cmd = "download_fastqs.py --errlog '{errlog}'--not-found-error -d '{file_download_dir}' -u '{dx_user_name}' -b '{barcode}' --dx-project-name '{dx_proj_name}' ".format(errlog=ERRLOG, file_download_dir=file_download_dir,dx_user_name=dx_user_name,barcode=barcode,dx_proj_name=dx_proj_name) 
		popen = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		stdout, stderr = popen.communicate()
		retcode = popen.returncode
		if retcode:
			print(stderr)

elif length_header == 4:
	for line in fh:
		line = line.strip("\n")
		if not line:
			continue
		if line.startswith("#"):
			continue
		input_dict = {}
		line = line.split("\t")
		uhts_run_name = line[0].strip()
		lane = line[1].strip()	
		library_name = line[2].strip()	
		barcode = line[3].strip()
		input_dict["uhts_run_name"] = uhts_run_name
		input_dict["lane"] = lane
		input_dict["library_name"] = library_name
		input_dict["barcode"] = barcode
		inputs.append(input_dict)

	for i in inputs:
		logger.info("Fetching FASTQs for " + str(i))
		run_name = i["uhts_run_name"]
		lib_name = i["library_name"]
		barcode = i["barcode"]	
		lane = i["lane"]
		cmd = "download_fastqs.py --errlog '{errlog}' --not-found-error -d '{file_download_dir}' -u '{dx_user_name}' --uhts-run-name '{run_name}' -l '{lib_name}' -b '{barcode}' --lane '{lane}' ".format(errlog=ERRLOG,file_download_dir=file_download_dir,dx_user_name=dx_user_name,run_name=run_name,lib_name=lib_name,barcode=barcode,lane=lane) 
		popen = subprocess.Popen(cmd,shell=True)
		stdout, stderr = popen.communicate()
		retcode = popen.returncode
		if retcode:
			print(stderr)
		
#fastq_dico: Keys are the file names of the FASTQs and values are the fully qualified paths to the FASTQs.
