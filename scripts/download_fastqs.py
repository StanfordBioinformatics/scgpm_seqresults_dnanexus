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
parser.add_argument('-l',"--library-name",required=True,help="The library name of the sample that was sequenced. This is name of the library that was submitted to SCGPM for sequencing. This is added as a property to all sequencing result projects through the 'library_name' property.")
parser.add_argument('-b',"--barcode",help="The barcode of the sequenced sample. If specified, then only FASTQs with this barcode will be downloaded. Otherwise, all FASTQs will be downloaded.")
parser.add_argument("-d","--file-download-dir",required=True,help="Local directory in which to download the FASTQ files.")

args = parser.parse_args()
dx_username = args.user_name
library_name = args.library_name
barcode = args.barcode
file_download_dir = args.file_download_dir
if not os.path.exists(file_download_dir):
	os.makedirs(file_download_dir)

dxsr = scgpm_seqresults_dnanexus.dnanexus_utils.DxSeqResults(dx_username=dx_username,library_name=library_name)
fastq_dico = dxsr.download_fastqs(barcode=barcode,dest_dir=file_download_dir)
#fastq_dico: Keys are the file names of the FASTQs and values are the fully qualified paths to the FASTQs.
