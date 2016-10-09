#!/usr/bin/env python
from argparse import ArgumentParser

import gbsc_dnanexus
import scgpm_seqresults_dnanexus.dnanexus_utils as u

DX_LOGIN_CONF = gbsc_dnanexus.CONF_FILE

description = ""
parser = ArgumentParser(description=description)
parser.add_argument('-u',"--user-name",required=True,help="The login name of the DNAnexus user, who has at least VIEW access to the DNAnexus project. An API token must have already been generated for this user and that token must have been added to the DNAnexus login configuration file located at {DX_LOGIN_CONF}.".format(DX_LOGIN_CONF=DX_LOGIN_CONF))
parser.add_argument("--dx-project-id",required=True,help="The DNAnexus ID of the project to download.")
parser.add_argument("--download-dir",required=True,help="Local directory in which to download the DNAnexus project.")

args = parser.parse_args()

dx_username = args.user_name
dx_project_id = args.dx_project_id
download_dir = args.download_dir

dxsr = u.DxSeqResults(dx_username=dx_username,dx_project_id=dx_project_id)
dxsr.download_project(download_dir=download_dir)


