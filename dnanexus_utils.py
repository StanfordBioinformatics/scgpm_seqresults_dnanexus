#!/usr/bin/env python

###
#Author: Nathaniel Watson
#2016-08-02
###

###
#ENVIRONMENT MODULES
#	1) gbsc/scgpm_seqresults_dnanexus/current
###

import pdb
import subprocess
import os
import sys
import logging
from argparse import ArgumentParser
import json


import dxpy #module load dx-toolkit/dx-toolkit

import scgpm_lims #module load scgpm_lims/current gbsc/limshostenv/prod
#The environment module gbsc/dnanexus/current should also be loaded in order to log into DNAnexus
import gbsc_dnanexus.utils #module load gbsc/gbsc_dnanexus/current


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:   %(message)s')
chandler = logging.StreamHandler(sys.stdout)
chandler.setLevel(logging.DEBUG)
chandler.setFormatter(formatter)
logger.addHandler(chandler)

class DxProjectMissingQueueProperty(Exception):
	pass

class DxMultipleProjectsWithSameLibraryName(Exception):
	pass

def accept_project_transfers(dx_username,access_level,queue,org,share_with_org=None):
	"""
	Function :
	Args     : dx_username - The DNAnexus login user name that is to receive pending transfers. An API token must have already been
								generated for this user and that token must have been added to the DNAnexus login configuration file located at 
								{DX_LOGIN_CONF}.".format(DX_LOGIN_CONF=DX_LOGIN_CONF))
						 access_level - Permissions level the new member should have on transferred projects. Should be one of 
						     ["VIEW","UPLOAD","CONTRIBUTE","ADMINISTER"]. See 
							   https://wiki.dnanexus.com/API-Specification-v1.0.0/Project-Permissions-and-Sharing for more details on access levels.
						 queue - str. The value of the queue property on a DNAnexus project. Only projects that are pending transfer that have
									   this value for the queue property will be transferred to the specified org.
						 org - The name of the DNAnexus org under which to accept the project transfers for projects that have their queue property
									 set to the value of the 'queue' argument.
						 share_with_org - Set this argument if you'd like to share the transferred projects with the org so that all users of the 
							 org will have access to the project. The value you supply should be the access level that members of the org will have.
	Returns  :
	"""
	dx_username = gbsc_dnanexus.utils.add_dx_userprefix(dx_username)
	gbsc_dnanexus.utils.log_into_dnanexus(dx_username)
	org = gbsc_dnanexus.utils.add_dx_orgprefix(org)
	pending_transfers = dxpy.api.user_describe(object_id=dx_username,input_params={"pendingTransfers": True})["pendingTransfers"]
	#pending_transfers is a list of project IDs
	transferred = []
	for proj_id in pending_transfers:
		dx_proj = dxpy.DXProject(proj_id)
		props = dx_proj.describe(input_params={"properties": True})["properties"]
		try:
			project_queue = props["queue"]	
		except KeyError:
			raise DxProjectMissingQueueProperty("DNAnexus project {proj_name} ({proj_id}) is missing the queue property.".format(proj_name=dx_proj.name,proj_id=proj_id))
		if queue != project_queue:
			continue
		logger.info("Accepting project transfer of {proj_name} ({proj_id}) for user {user}, to be billed under the org {org}.".format(proj_name=dx_proj.name,proj_id=proj_id,user=dx_username,org=org))
		dxpy.DXHTTPRequest("/" + proj_id + "/acceptTransfer", {"billTo": org })
		transferred.append(dx_proj.name)
		if share_with_org:
			logger.info("Sharing project {proj_id} with {org} with access level {share_with_org}.".format(proj_id=proj_id,org=org,share_with_org=share_with_org))
			dxpy.api.project_invite(object_id=proj_id,input_params={"invitee": org,"level": share_with_org})
	return transferred

	

class DnanexusBarcodeNotFound(Exception):
	pass

class DxSeqResults:
	UHTS = scgpm_lims.Connection()
	#SNYDER_ENCODE_ORG = "org-snyder_encode"
	LOG_LEVELS = [x for x in logging._levelNames if isinstance(x,str)]
	LOGGER_LEVEL = logging.DEBUG #accept all messages sent to it
	DEFAULT_HANDLER_LEVEL = logging.DEBUG
	DX_RAW_DATA_FOLDER = "/raw_data"
	DX_BCL2FASTQ_FOLDER = "/stage0_bcl2fastq"
	DX_SAMPLESHEET_DIR = os.path.join(DX_BCL2FASTQ_FOLDER,"miscellany")
	DX_FASTQ_FOLDER = os.path.join(DX_BCL2FASTQ_FOLDER,"fastqs")
	DX_FASTQC_FOLDER = "/stage1_qc/fastqc_reports"
	DX_QC_REPORT_FOLDER = "/stage2_qc_report"

	def __init__(self,dx_username,dx_project_id=False,dx_project_name=False,library_name=False,billing_account_id=None):
		"""
		Description : Logs the specified user into DNAnexus, and then finds the DNAnexus sequencing results project that was uploaded by 
									SCGPM. The project can be precisely retrieved if the projecd ID is specified (via the dx_project_id argument).
									Otherwise, you can uhe dx_project_name argument if you know the name, or use the library_name argument if you know the
								  name of the library that was submitted to the SCGPM sequencing center. All sequencing
									result projects uploaded to DNAnexus by SCGPM contain a property named 'library_name', and projects will be searched
									on this property for a matching library name when the library_name argument is specified. If both the library_name
								  and the dx_project_name arguments are specified, only the latter is used in finding a project match. The
								  billing_account argument can optionally be specifed to restrict all project searches to only those that are
									billed to that particular billing account (unless dx_project_id is specified in which case the DNAnexus project is
									directly retrieved).
	  Args : dx_username - str. The login name of a DNAnexus user.
		Args : dx_project_id - str. The ID of the DNAnexus project. If specified, no project search will be performed as it will be
						directly retrieved.
					 dx_project_name - the name of a DNAnexus project containing sequencing results that were uploaded by SCGPM. 
					 library_name - str. The library name of the sample that was sequenced. This is name of the library that was 
														submitted to SCGPM for sequencing. This is added as a property to all sequencing result projects through
														the 'library_name' property.
					 billing_account_id - The name of the DNAnexus billing account that the project belongs to. This will only be used to restrict 
						the search of projects that the user can see to only those billed by the specified account.
		"""
		self.dx_username = gbsc_dnanexus_utils.add_dx_userprefix(dx_username)
		self.billing_account_id = billing_account_id
		if self.billing_account_id:
			gbsc_dnanexus.utils.validate_billing_to_prefix(billing_account_id=self.billing_account_id,exception=True)
		if not self.billing_account_id:
			self.billing_account_id = None
			#Making sure its set to None in this case, b/c the user could have passed in an empty string.
			# Needs to be None instead b/c dxpy calls that refernce the billing account don't work if this is set to the empty string. None
			# just means the user doesn't care about which billing account.
	
		#LOG INTO DNANEXUS FIRST
		gbsc_dnanexus.utils.log_into_dnanexus(self.dx_username)
		self.dx_project_id = dx_project_id
		self.dx_project_name = dx_project_name
		self.library_name = library_name
		if not self.dx_project_id and not self.dx_project_name and not self.library_name:
			raise Exception("One of the arguments 'dx_project_id', 'dx_project_name' or 'library_name' must be specified.")
		self._set_dxproject_id()
		#_set_dxproject_id sets the following instance attributes:
		# self.project_id
		# self.dx_project_name
		# self.library_name
		self._set_sequencing_run_name() #sets self.sequencing_run_name.
		self._set_sequencing_platform() #sets self.sequencing_platform

	def _set_dxproject_id(self):
		"""
		Function : Retrieves the ID of the project in DNAnexus that has the sequencing results for the library specified by
							 self.library_name. It does this by finding the project whose property named 'library_name' is set to
							 self.library_name.  May return None if there isn't yet a project found in DNAnexus yet, which indicates that the
							 sequencing likely hasn't finished yet.
		Returns  : str. The DNAnexus project ID or the empty string if a project wasn't found.
		Raises   : scgpm_seqresults_dnanexus.dnanexus_utils.DxMultipleProjectsWithSameLibraryName() if the search is by self.library_name, and multiple DNAnexus projects have that library name.
		"""
		dx_proj = ""
		if self.dx_project_id:
			dx_proj = dxpy.DXProject(dxid=self.dx_project_id)
		elif self.dx_project_name:
			res = dxpy.find_one_project(billed_to=self.billing_account_id,zero_ok=True,more_ok=True,name=self.dx_project_name)
			if res:
				dx_proj = dxpy.DXProject(dxid=res["id"])
		else:
			res = dxpy.find_projects(billed_to=self.billing_account_id,zero_ok=True,more_ok=True,properties={"library_name":self.library_name})
			if len(res) > 1:
				projects = [x.id for x in res]
				raise DxMultipleProjectsWithSameLibraryName("Error - Multiple DNAnexus projects have the same value for the library_name property value of {library_name}. The projects are {projects}.".format(library_name=self.library_name,projects=projects))
			if res:
				dx_proj = dxpy.DXProject(dxid=res[0]["id"])

		if not dx_proj:
			return

		self.dx_project_id = dx_proj.id
		self.dx_project_name = dx_proj.name
		self.library_name = dxpy.api.project_describe(object_id=dx_proj.id,input_params={"fields": {"properties": True}})["properties"]["library_name"]

	def _set_sequencing_run_name(self):
		"""
		Function : Sets the self.sequencing_run_name attribute to the name of the sequencing run in UHTS.
		"""
		run_name = self.UHTS.get_runinfo_by_library_name(library_name=self.library_name).keys()[0]
		self.sequencing_run_name = run_name

	def _set_sequencing_platform(self):
		"""
		Function : Sets the self.sequencing_platform attribute to the sequencing platform name.
							 Currently, only knows about the HiSeq2000 and HiSeq4000 platforms.
		Raises   : Exception if the platform is not recognized.
		"""
		ri = self.UHTS.getruninfo(self.sequencing_run_name)["run_info"]
		platform = ri["platform"]
		if platform == "hiseq4000":
			platform == "HiSeq4000"
		elif platform == "hiseq2000":
			platform == "HiSeq2000"
		else:
			raise Exception("Unknown platform {platform} for sequencing run {run}".format(platform=platform,run=self.sequencing_run_name))
		self.sequencing_platform = platform

	def get_run_details_json(self):
		"""
		Function : Retrieves the JSON object for the stats in the file named run_details.json in the project specified by self.project_id.
		Returns  : JSON object of the run details.
		"""
		run_details_json_filename = "run_details.json"
		run_details_json_id = dxpy.find_one_data_object(more_ok=False,zero_ok=True,project=self.project_id,name=run_details_json_filename)["id"]
		dxpy.download_dxfile(show_progress=True,dxid=run_details_json_id,project=self.project_id,filename=run_details_json_filename)
		fh = open(run_details_json_filename,'r')
		run_details_json = json.load(fh)
		return run_details_json
	
	
	def get_sample_stats_json(self,barcode=None):
		"""
		Function : Retrieves the JSON object for the stats in the file named sample_stats.json in the project specified by self.project_id.
							 barcode - str. The barcode for the sample.
		Returns  : A list of dicts if barcode=None, otherwise a dict for the given barcode.
		"""
		sample_stats_json_filename = "sample_stats.json"
		sample_stats_json_id = dxpy.find_one_data_object(more_ok=False,zero_ok=False,project=self.project_id,name=sample_stats_json_filename)["id"]
		dxpy.download_dxfile(dxid=sample_stats_json_id,project=self.project_id,filename=sample_stats_json_filename)
		fh = open(sample_stats_json_filename,'r')
		sample_stats_json = json.load(fh)
	
		if not barcode:
			return sample_stats_json
	
		for d in sample_stats_json:
			sample_barcode = d["Sample name"]
			if sample_barcode == barcode:
				return d
		if barcode:
			raise DnanexusBarcodeNotFound("Barcode {barcode} for {library_name} not found in {sample_stats_json_filename} in project {project}.".format(barcode=barcode,library_name=self.library_name,sample_stats_json_filename=sample_stats_json_filename,project=self.project_id))

	def download_metadata_tar(self,download_dir):	
		"""
		Function : Downloads the ${run_name}.metadata.tar file from the DNAnexus sequencing results project.
		Args     : download_dir - The local directory path to download the QC report to.
		Returns  : str. The filepath to the downloaded metadata tarball.
		"""
		is not os.path.isdir(download_dir):
			os.makedirs(download_dir)	
		res = dxpy.find_one_data_object(project=self.project_id,folder=self.self.DX_RAW_DATA_FOLDER,name="*metadata.tar",name_mode="glob")
		#res will be something like {u'project': u'project-BzqVkxj08kVZbPXk54X0P2JY', u'id': u'file-BzqVkg800Fb0z4437GXJfGY6'}
		#dxpy.find_one_data_object() raises a dxpy.exceptions.DXSearchError() if nothing is found.
		dx_file = dxpy.DXFile(dxid=res["id"],project=res["project"])
		download_file_name = os.path.join(download_dir,dx_file.name)
		dxpy.bindings.dxfile_functions.download_dxfile(dxid=dx_file,filename=dx_file.name)
		return download_file_name

	def download_run_details_json(self,download_dir):
		"""
		Function : Downloads the run_details.json and the barcodes.json from the DNAnexus sequencing results project.
		Args     : download_dir - The local directory path to download the QC report to.
		Returns  : str. The filepath to the downloaded run_details.json file.
		"""
		is not os.path.isdir(download_dir):
			os.makedirs(download_dir)	
		res = dxpy.find_one_data_object(project=self.project_id,folder=self.self.DX_QC_REPORT_FOLDER,name="run_details.json",name_mode="exact")
		#res will be something like {u'project': u'project-BzqVkxj08kVZbPXk54X0P2JY', u'id': u'file-BzqVkg800Fb0z4437GXJfGY6'}
		#dxpy.find_one_data_object() raises a dxpy.exceptions.DXSearchError() if nothing is found.
		dx_file = dxpy.DXFile(dxid=res["id"],project=res["project"])
		download_file_name = os.path.join(download_dir,dx_file.name)
		dxpy.bindings.dxfile_functions.download_dxfile(dxid=dx_file,filename=dx_file.name)
		return download_file_name

	def download_barcodes_json(self,download_dir):
		"""
		Function : Downloads the run_details.json and the barcodes.json from the DNAnexus sequencing results project.
		Args     : download_dir - The local directory path to download the QC report to.
		Returns  : str. The filepath to the downloaded barcodes.json file.
		"""
		is not os.path.isdir(download_dir):
			os.makedirs(download_dir)	
		res = dxpy.find_one_data_object(project=self.project_id,folder=self.self.DX_QC_REPORT_FOLDER,name="barcodes.json",name_mode="exact")
		#res will be something like {u'project': u'project-BzqVkxj08kVZbPXk54X0P2JY', u'id': u'file-BzqVkg800Fb0z4437GXJfGY6'}
		#dxpy.find_one_data_object() raises a dxpy.exceptions.DXSearchError() if nothing is found.
		dx_file = dxpy.DXFile(dxid=res["id"],project=res["project"])
		download_file_name = os.path.join(download_dir,dx_file.name)
		dxpy.bindings.dxfile_functions.download_dxfile(dxid=dx_file,filename=dx_file.name)
		return download_file_name

	def download_samplesheet(self,download_dir):
		"""
		Function : Downloads the SampleSheet used in demultiplexing from the DNAnexus sequencing results project.
		Args     : download_dir - The local directory path to download the QC report to.
		Returns  : str. The filepath to the downloaded QC report.
		"""
		is not os.path.isdir(download_dir):
			os.makedirs(download_dir)	
		res = dxpy.find_one_data_object(project=self.project_id,folder=self.DX_SAMPLESHEET_FOLDER,name="*_samplesheet.csv",name_mode="glob")
		#res will be something like {u'project': u'project-BzqVkxj08kVZbPXk54X0P2JY', u'id': u'file-BzqVkg800Fb0z4437GXJfGY6'}
		#dxpy.find_one_data_object() raises a dxpy.exceptions.DXSearchError() if nothing is found.
		dx_file = dxpy.DXFile(dxid=res["id"],project=res["project"])
		download_file_name = os.path.join(download_dir,dx_file.name)
		dxpy.bindings.dxfile_functions.download_dxfile(dxid=dx_file,filename=dx_file.name)
		return download_file_name

	def download_qc_report(self,download_dir):
		"""
		Function : Downloads the QC report from the DNAnexus sequencing results project.
		Args     : download_dir - The local directory path to download the QC report to.
		Returns  : str. The filepath to the downloaded QC report.
		"""
		is not os.path.isdir(download_dir):
			os.makedirs(download_dir)	
		res = dxpy.find_one_data_object(project=self.project_id,folder=self.DX_QC_REPORT_FOLDER,name="*_QC_Report.pdf",name_mode="glob")
		#res will be something like {u'project': u'project-BzqVkxj08kVZbPXk54X0P2JY', u'id': u'file-BzqVkg800Fb0z4437GXJfGY6'}
		#dxpy.find_one_data_object() raises a dxpy.exceptions.DXSearchError() if nothing is found.
		dx_file = dxpy.DXFile(dxid=res["id"],project=res["project"])
		download_file_name = os.path.join(download_dir,dx_file.name)
		dxpy.bindings.dxfile_functions.download_dxfile(dxid=dx_file,filename=dx_file.name)
		return download_file_name

	def download_fastqc_reports(self,download_dir):
		"""
		Function : Downloads the QC report from the DNAnexus sequencing results project.
		Args     : download_dir - The local directory path to download the QC report to.
		Returns  : str. The filepath to the downloaded FASTQC reports folder.
		"""
		is not os.path.isdir(download_dir):
			os.makedirs(download_dir)	
		cmd = "dx download {proj_id}{folder} -o {download_dir}".format(proj_id=self.dx_project_id,folder=self.DX_FASTQC_FOLDER,download_dir=download_dir)
		subprocess.check_call(cmd,shell=True)
		#rename the downloaded folder to ${download_dir}/FASTQC
		os.rename(os.path.join(download_dir,self.DX_FASTQC_FOLDER.lstrip("/")),os.path.join(download_dir,"FASTQC"))
		return os.path.join(download_dir,"FASTQC")

	def download_project(self,download_dir):
		"""
		Function :
		Args     :
		Returns  :
		"""
		if not os.path.isdir(download_dir):
			os.makedirs(download_dir)
	  cmd = "dx download {proj_id}{folder} -o {download_dir}".format(proj_id=self.dx_project_id,folder=self.DX_BCL2FASTQ_FOLDER,download_dir=download_dir)
		subprocess.check_call(cmd,shell=True)
		#rename the downloaded folder to ${download_dir}/FASTQ
		os.rename(os.path.join(download_dir,self.DX_BCL2FASTQ_FOLDER.lstrip("/")),os.path.join(download_dir,"FASTQ"))
		#download the FASTQC files
		self.download_fastqc_reports(download_dir=download_dir)
		#download the in-house QC report
		self.download_qc_report(download_dir=download_dir)
		#download the SampleSheet used in demultiplexing
		self.download_samplesheet(download_dir=download_dir)
		#download the run_details.json
		self.download_run_details_json(download_dir=download_dir)
		#download the barcodes.json
		self.download_barcodes_json(download_dir=download_dir)
		#download the ${run_name}.metadata.tar file.
		self.download_metadata_tar(download_dir=download_dir)
		
	
	def download_fastqs(self,dest_dir,barcode="",overwrite=False):
		"""
		Function : Downloads all FASTQ files in the project that match the specified barcode, or if a barcode isn't given, all FASTQ files as in this case it is assumed that this is not
							 a multiplexed experiment. Files are downloaded to the directory specified by dest_dir. 
		Args     : barcode - str. The barcode sequence used. If not set, then it is assumed that barcodes were not used (no multiplexing). 
							 dest_dir - The local directory in which the FASTQs will be downloaded.
							 overwrite - bool. If True, then if the file to download already exists in dest_dir, the file will be 
										downloaded again, overwriting it. If False, the file will not be downloaded again from DNAnexus.
		Returns  : dict. Keys are the barcode names, or if non-barcoded, the read number names. 
		Raises   : Exception() if barcode is specified and less than or greater than 2 FASTQ files are found.
		"""
		barcode_glob = "*_{barcode}_*".format(barcode=barcode)
		if barcode:
			fastqs= dxpy.find_data_objects(project=self.project_id,folder=self.DX_FASTQ_FOLDER,name=barcode_glob,name_mode="glob")
		else:
			fastqs= dxpy.find_data_objects(project=self.project_id,folder=self.DX_FASTQ_FOLDER,name="*.fastq.gz",name_mode="glob")
		fastqs = [dxpy.DXFile(project=x["project"],dxid=x["id"]) for x in fastqs]
		if not len(fastqs):
			msg = "No FASTQ files found for run {run} ".format(run=proj_name)
			if barcode:
				msg += "and barcode {barcode}.".format(barcode=barcode)
			raise Exception(msg)
		if len(fastqs) != 2 and barcode:
			raise Exception("Expected at most two FASTQ files for a given barcode - one for the foward reads and and another for the reverse reads.")

		dico = {}
	
		for f in fastqs:
			props = dxpy.api.file_describe(object_id=f.id, input_params={"fields": {"properties": True}})["properties"]
			read_num = int(props["read"])
			barcode = props["barcode"]
			name = f.name
			filedest = os.path.abspath(os.path.join(dest_dir,name))
			if os.path.exists(filedest):
				if overwrite:
					print("Downloading FASTQ file {name} from DNAnexus project {project} to {path}.".format(name=f.name,project=self.dx_project_name,path=filedest))
					dxpy.download_dxfile(f,filedest)
			else:
				print("Downloading FASTQ file {name} from DNAnexus project {project} to {path}.".format(name=f.name,project=self.dx_project_name,path=filedest))
				dxpy.download_dxfile(f,filedest)

			if barcode:
				if barcode not in dico:
					dico[barcode] = {}
				if read_num in dico[barcode]:
					raise Exception("Found mutliple FASTQ files with read number {read_num} for barcode {barcode}, and expected only one.".format(read_num=read_num,barcode=barcode))
				dico[barcode][read_num] = filedest
			else:
				if read_num in dico:
					raise Exception("Found mutliple FASTQ files with read number {read_num}, and expected only one. If this is a multiplexed run, be sure to specify the barcode.".format(read_num=read_num))
				dico[read_num] = filedest
		return dico
			

		
				

#logger = logging.getLogger(__name__)
#logger.setLevel(LOGGER_LEVEL)
#formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:   %(message)s')
#fhandler = logging.FileHandler(filename=logFile,mode='a')
#fhandler.setLevel(logLevel)
#fhandler.setFormatter(formatter)
#chandler = logging.StreamHandler(sys.stdout)
#chandler.setLevel(logLevel)
#chandler.setFormatter(formatter)
#logger.addHandler(fhandler)
#logger.addHandler(chandler)
