#!/usr/bin/env python
from argparse import ArgumentParser
import logging
import sys

import dxpy

import gbsc_dnanexus
import scgpm_seqresults_dnanexus.dnanexus_utils as u

DX_LOGIN_CONF = gbsc_dnanexus.CONF_FILE

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:\t%(message)s')
chandler = logging.StreamHandler(sys.stdout)
chandler.setLevel(logging.DEBUG)
chandler.setFormatter(formatter)
logger.addHandler(chandler)

description = "Downloads a SCGPM sequencing results project from DNAnexus. Currently, there is one DNAnexus project for each lane of Illumina sequencing. A folder will be created by the name of the DNAnexus project within the specified output folder. The project folder will contain a FASTQ subfolder, a FASTQC subfolder, and several files including 1) the sequencing QC report, 2) the list of barcodes in the sequencing lane in barcodes.json, run information in run_details.json, and a meta-data tarball by the name of ${sequencing_run_name}.metadata.tar. This last file contains important XML files output by the sequencer, such as the runParameters.XML and RunInfo.xml."

parser = ArgumentParser(description=description)
parser.add_argument("-u","--user-name",required=True,help="The login name of the DNAnexus user, who has at least VIEW access to the DNAnexus project. An API token must have already been generated for this user and that token must have been added to the DNAnexus login configuration file located at {DX_LOGIN_CONF}.".format(DX_LOGIN_CONF=DX_LOGIN_CONF))
parser.add_argument("--download-dir",required=True,help="Local directory in which to download the DNAnexus project.")
parser.add_argument("-l","--logfile",required=True,help="The name of the log file. Will be opened in append mode.")
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("--dx-project-id",help="The DNAnexus ID of the project to download.")
group.add_argument("--dx-project-list",help="File with DNAnexus project IDs, one per line, for batch project download. Empty lines and lines starting with a '#' will be ignored.")

args = parser.parse_args()

dx_username = args.user_name
dx_project_id = args.dx_project_id
dx_project_list= args.dx_project_list
download_dir = args.download_dir
logfile = args.logfile
fhandler = logging.FileHandler(filename=logfile,mode="a")
fhandler.setLevel(logging.INFO)
fhandler.setFormatter(formatter)
logger.addHandler(fhandler)

dx_project_ids = []
if dx_project_id:
	dx_project_ids.append(dx_project_id)
else:
	fh = open(dx_project_list)
	for line in fh:
		line = line.strip("\n")
		if not line:
			continue	
		if line.startswith("#"):
			continue
		dx_project_ids.append(line.strip())
	fh.close()

for i in dx_project_ids:
	dxsr = u.DxSeqResults(dx_username=dx_username,dx_project_id=dx_project_id)
	dxsr.download_project(download_dir=download_dir)


