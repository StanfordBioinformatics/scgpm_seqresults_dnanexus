#!/usr/bin/env python

###
#Nathaniel Watson
#2016-11-17
###

from argparse import ArgumentParser
import os
import sys

import scgpm_seqresults_dnanexus.dnanexus_utils
import gbsc_dnanexus

DX_LOGIN_CONF = gbsc_dnanexus.CONF_FILE

description = "Given a tab-delimited input file with columns run name, lane, and barcode"

parser = ArgumentParser(description=description)
parser.add_argument("-i","--infile",required=True,help="Tab-delimited input file with columns uhts run name, lane, and barcode. Empty lines and lines beginning with '#' are ignored. A field-header line starting with '#' is required as the first line.")
parser.add_argument("--fieldindex-uhts-run-name",required=True,type=int,help="The 0-base index of the uhts run name field in the input file.")
parser.add_argument("--fieldindex-lane",required=True,type=int,help="The 0-base index of the lane field in the input file.")
parser.add_argument("--fieldindex-barcode",required=True,type=int,help="The 0-base index of the barcode field in the input file.")
parser.add_argument("--fastq-dir",required=True,help="The directory containing DNAnexus sequencing results projects (that were download from DNAnexus).")
parser.add_argument("-u","--username",required=True,help="The login name of the DNAnexus user, who has at least VIEW access to the DNAnexus project. An API token must have already been generated for this user and that token must have been added to the DNAnexus login configuration file located at {DX_LOGIN_CONF}.".format(DX_LOGIN_CONF=DX_LOGIN_CONF))
parser.add_argument("-o","--outfile",required=True)

args = parser.parse_args()
infile = args.infile
run_name_field_index = args.fieldindex_uhts_run_name
lane_field_index = args.fieldindex_lane
barcode_field_index = args.fieldindex_barcode

fastq_dir = args.fastq_dir
dx_username = args.username
outfile = args.outfile
fout = open(outfile,'w')
fh = open(outfile,"w")

if not os.path.exists(fastq_dir):
	raise Exception("Path provided to --fastq-dir ({path}) does not exist.".format(path=fastq_dir))

fh = open(infile)
header = fh.readline()
if not header.startswith("#"):
	raise Exception("Missing header field-header line starting with '#' as first line in --infile.")

fastq_dir_contents = os.listdir(fastq_dir)
if not fastq_dir_contents:
	raise Exception("There aren't any FASTQ files in --fastq-dir ({fastq_dir}).".format(fastq_dir=fastq_dir))

index = 0
dico = {}
for line in fh:
	index += 1
	line =  line.strip("\n")
	dico[index] = {}
	dico[index]["line"] = line
	dico[index]["fastq_files"] = {}

for i in sorted(dico):
	line = dico[i]["line"]
	if not line or line.startswith("#"):
		continue	
	line = line.split("\t")
	run_name = line[run_name_field_index].strip()
	lane = line[lane_field_index].strip()
	barcode = line[barcode_field_index].strip()
	dxsr = scgpm_seqresults_dnanexus.dnanexus_utils.DxSeqResults(dx_username=dx_username,uhts_run_name=run_name,sequencing_lane=lane)
	if not dxsr.dx_project_id:
		#no project found.
		continue
	fastq_files_props = dxsr.get_fastq_files_props(barcode=barcode)
	for prop in fastq_files_props: 
		#i is the DNAnexus object ID of the FASTQ file.
		fastq_props = fastq_files_props[prop]
		read_num = int(fastq_props["read"])
		file_name = fastq_props["fastq_file_name"]
		if file_name in fastq_dir_contents:
			dico[i]["fastq_files"][read_num] = file_name

for i in sorted(dico):
	data = dico[i]
	line = dico[i]["line"]
	if data["fastq_files"]:
		for j in sorted(data["fastq_files"]):
			file_name = data["fastq_files"][j]
			fout.write("\t".join([file_name,str(read_num),line]) + "\n")
	else:
		fout.write("\t\t" + line + "\n")
fout.close()
	

