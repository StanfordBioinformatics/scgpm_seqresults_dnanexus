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

AWARD="U54HG006996"
HEADER = "aliases:array	dataset	replicate	submitted_file_name	paired_end	paired_with	machine	flowcell	lane	barcode	controlled_by	file_format	output_type	run_type	read_length	platform	lab	award"

description = ""
parser = ArgumentParser(description=description)

parser.add_argument('-u',"--user-name",required=True,help="DNAnexus user name. The login name of the DNAnexus account. An API token must have already been generated for this user and that token must have been added to the DNAnexus login configuration file located at {DX_LOGIN_CONF}.".format(DX_LOGIN_CONF=DX_LOGIN_CONF))
parser.add_argument("-i","--infile",required=True,help="Tab-delimited file with the following columns: 1) project name for the run in DNAnexus, 2) barcode, and 3) platform. Must have a field-header line as the first line. The platform field must be of the form ENCODE:HiSeq2000 or ENCODE:HiSeq4000.")
parser.add_argument("-d","--file-download-dir",required=True,help="Local directory in which to download the FASTQ files.")
parser.add_argument("-o","--outfile",required=True,help="Output file. Will be opened in append mode.")

args = parser.parse_args()

laneReg = re.compile(r'_L(\d)_')
readNumReg = re.compile(r'_R(\d)')

dx_username = args.user_name
subprocess.check_call("log_into_dnanexus.sh -u {user}".format(user=dx_username),shell=True)

download_dir = args.file_download_dir
if not os.path.exists(download_dir):
	os.makedirs(download_dir)
outfile = args.outfile
write_header = False
if not os.path.exists(outfile):
	write_header = True
#fout = open(outfile,'a')
#if write_header:
#	fout.write(HEADER + "\n")

infile = args.infile
fh = open(infile,'r')
header = fh.readline()
for line in fh:
	line = line.strip("\n")
	if not line:
		continue
	line = line.split("\t")
	proj_name = line[0].strip()
	barcode = line[1].strip()
	platform = line[2].strip()
	proj_id = dxpy.find_one_project(more_ok=False,name=proj_name)['id']
	proj = dxpy.DXProject(proj_id)
	proj_name = proj.name
	lane = laneReg.search(proj_name).groups()[0]
	flowcell = proj_name.rsplit("_")[-3]
	machine = proj_name.split("_")[1]
	dx_seqres = encode_dx_utils.DxSeqResults(dnanexus_username=dx_username,project_name=proj_name)
	downloaded_fastqs = dx_seqres.download_fastqs(barcode=barcode,"Bob")
	if not len(download_fastqs):
		raise Exception("No FASTQ files found for run {run} and barcode {barcode}.".format(run=proj_name,barcode=barcode))
	#for fastq_name in downloaded_fastqs:
#		fastq_path = downloaded_fastqs[fastq_name]
#		try:
#			read_num = readNumReg.search(fastq_name).groups()[0]
#		except AttributeError as e:
#			raise
#		alias = "michael-snyder:" + fastq_name
#		fout.write("{alias}\t\t\t{dest}\t{read_num}\t\t{machine}\t{flowcell}\t{lane}\t{barcode}\t\tfastq\treads\tpaired-ended\t101\tENCODE:HiSeq{platform}\tmichael-snyder\t{AWARD}\n".format(alias=alias,dest=dest,read_num=read_num,machine=machine,flowcell=flowcell,lane=lane,barcode=barcode,platform=platform,AWARD=AWARD))
#		#print(f.describe())
#		logger.info("Downloading file {name}".format(name=name))
#		dxpy.download_dxfile(f,dest)
#fout.close()
#
