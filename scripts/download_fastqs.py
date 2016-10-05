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

import encode.upload_seq_results_to_syapse.dnanexus_utils as encode_dx_utils
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

parser.add_argument('-u',"--user-name",required=True,help="DNAnexus user name. The login name of the DNAnexus account. An API token must have already been generated for this user and that token must have been added to the DNAnexus login configuration file located at {DX_LOGIN_CONF}.".format(DX_LOGIN_CONF=DX_LOGIN_CONF))
parser.add_argument('-s',"--seq-request-uid",required=True,help="The Syapse SequencingRequest UID.")
parser.add_argument('-b',"--barcode",help="The barcode of the sequenced sample. If specified, then only FASTQs with this barcode will be downloaded. Otherwise, all FASTQs will be downloaded.")
parser.add_argument("-d","--file-download-dir",required=True,help="Local directory in which to download the FASTQ files.")

args = parser.parse_args()
dx_username = args.user_name
sreq_id = args.seq_request_uid
barcode = args.barcode
file_download_dir = args.file_download_dir
if not os.path.exists(file_download_dir):
	os.makedirs(file_download_dir)

dxsr = encode_dx_utils.DxSeqResults(dx_username=dx_username,sreq_id=sreq_id)
fastq_dico = dxsr.download_fastqs(barcode=barcode,dest_dir=file_download_dir)
#fastq_dico: Keys are the file names of the FASTQs and values are the fully qualified paths to the FASTQs.
