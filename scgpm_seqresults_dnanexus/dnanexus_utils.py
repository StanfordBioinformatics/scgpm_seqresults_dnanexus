# -*- coding: utf-8 -*- 

###
#Author: Nathaniel Watson
#2016-08-02
###

###
#ENVIRONMENT MODULES
#  1) gbsc/scgpm_seqresults_dnanexus/current
###

import json
import logging
import os
import pdb
from io import StringIO
import subprocess
import sys
import time


import dxpy #module load dx-toolkit/dx-toolkit

import scgpm_seqresults_dnanexus.picard_tools as picard
import scgpm_seqresults_dnanexus as sd
import scgpm_seqresults_dnanexus.log as sd_log
import gbsc_dnanexus.utils  #gbsc_dnanexus git submodule containing utils Python module that can be used to log into DNAnexus.

success_logger = logging.getLogger("success")
success_logger.setLevel(logging.INFO)
sd_log.add_file_handler(logger=success_logger,level=logging.INFO,tags=["success"])

debug_logger = logging.getLogger(__name__)

def log_success_and_debug(msg):
    debug_logger.debug(msg)
    success_logger.info(msg)

class DxMissingAlignmentSummaryMetrics(Exception):
    """
    Raised by `DxSeqResults.get_alignment_summary_metrics()`	when it can't locate a Picard alignment summary
    metrics file for a given barcoded sample of FASTQ sequencing results. 
    """

class DxMissingLibraryNameProperty(Exception):
    """
    Raised when creating a new DxSeqResults instance for a DNAnexus project that doesn't have the
    library_name project property present.
    """
    pass

class DxProjectMissingQueueProperty(Exception):
    pass

class DxMultipleProjectsWithSameLibraryName(Exception):
    pass

class FastqNotFound(Exception):

    #Can be raised whenever we look for specific FASTQ files in a DNAnexus project, but they aren't there. 
    pass

class DnanexusBarcodeNotFound(Exception):
    pass

def select_newest_project(dx_project_ids):
    """
    Given a list of DNAnexus project IDs, returns the one that is newest as determined by creation date.
  
    Args: 
        dx_project_ids: `list` of DNAnexus project IDs.
  
    Returns:
        `str`.
    """
    if len(dx_project_ids) == 1:
        return dx_project_ids[0]
    
    projects = [dxpy.DXProject(x) for x in dx_project_ids]
    created_times = [x.describe()["created"] for x in projects]
    paired = zip(created_times,projects)
    paired.sort(reverse=True)
    return paired[0][0]

def accept_project_transfers(access_level,queue,org,share_with_org=None):
      """
      Args:
          access_level: `str`. Permissions level the new member should have on transferred projects. Should 
              be one of ["VIEW","UPLOAD","CONTRIBUTE","ADMINISTER"]. See 
              https://wiki.dnanexus.com/API-Specification-v1.0.0/Project-Permissions-and-Sharing for more details on access levels.
          queue: `str`. The value of the queue property on a DNAnexus project. Only projects that are 
              pending transfer that have this value for the queue property will be transferred to the 
              specified org.
          org: `str`. The name of the DNAnexus org under which to accept the project transfers for projects 
              that have their queue property set to the value of the 'queue' argument.
          share_with_org: `str`. Set this argument if you'd like to share the transferred projects 
              with the org so that all users of the org will have access to the project. The value you 
              supply should be the access level that members of the org will have.
      Returns:
          `dict`: The projects that were transferred to the specified billing account. Keys are the 
          project IDs, and values are the project names. 
      """
      dx_username = gbsc_dnanexus.utils.get_dx_username()
      #gbsc_dnanexus.utils.log_into_dnanexus(dx_username)
      org = gbsc_dnanexus.utils.add_dx_orgprefix(org)
      pending_transfers = gbsc_dnanexus.utils.pending_transfers(dx_username)
      #pending_transfers is a list of project IDs
      transferred = {}
      for proj_id in pending_transfers:
          dx_proj = dxpy.DXProject(proj_id)
          props = dx_proj.describe(input_params={"properties": True})["properties"]
          try:
              project_queue = props["queue"]  
          except KeyError:
              raise DxProjectMissingQueueProperty("DNAnexus project {proj_name} ({proj_id}) is missing the queue property.".format(proj_name=dx_proj.name,proj_id=proj_id))
          if queue != project_queue:
              continue
          msg = "Accepting project transfer of {proj_name} ({proj_id}) for user {user}, to be billed under the org {org}.".format(proj_name=dx_proj.name,proj_id=proj_id,user=dx_username,org=org)
          debug_logger.debug(msg)
          dxpy.DXHTTPRequest("/" + proj_id + "/acceptTransfer", {"billTo": org })
          success_logger.info(msg)
          transferred[proj_id] = dx_proj.name
          if share_with_org:
              msg = "Sharing project {proj_id} with {org} with access level {share_with_org}.".format(proj_id=proj_id,org=org,share_with_org=share_with_org)
              debug_logger.debug(msg)
              share_with_org(project_ids=[proj_id], org=org, access_level=share_with_org)
              dxpy.api.project_invite(object_id=proj_id,input_params={"invitee": org,"level": share_with_org,"suppressEmailNotification": True})
              success_logger.info(msg)
      return transferred

def find_org_projects_by_name_glob(org, glob):
    """
    Args:
        glob: `str`. 

    Ex:
        Find the project(s) with SREQ-163 at the end of the project's name:
            find_org_projects_by_name_glob(org="org-someorg", glob="*SREQ-163")
    """
    results = dxpy.api.org_find_projects(object_id=org, input_params={"name": {"glob": glob}})["results"]
    return [i["id"] for i in results]

def share_with_org(project_ids, org, access_level, suppress_email_notification=False):
    """
    Shares one or more DNAnexus projects with an organization. It appears that DNAnexus requires 
    for the user that wants to share the org to first have ADMINISTER access on the project. Only
    then could he share the project with the org. 

    Args:
        project_ids: `list`. One or more DNAnexus project identifiers, where each project ID is in 
            the form "project-FXq6B809p5jKzp2vJkjkKvg3". 
        org: `str`. The name of the DNAnexus org with which to share the projects. 
        access_level: The permission level to give to members of the org - one of
            ["VIEW","UPLOAD","CONTRIBUTE","ADMINISTER"].
        suppress_email_notification: `bool`. True means to allow the DNAnexus platform to send an
            email notification for each shared project. 
    """
    for p in project_ids:
        # First give current user ADMINISTER access to project. For this to be able to work, user
        # must already be an admin of the org. 
        dxpy.api.project_invite(object_id=p,input_params={"invitee": dxpy.whoami(),"level": "ADMINISTER","suppressEmailNotification": suppress_email_notification})
        dxpy.api.project_invite(object_id=p,input_params={"invitee": org,"level": access_level,"suppressEmailNotification": suppress_email_notification})
 

class DxSeqResults:
    """
    Finds the DNAnexus sequencing results project that was uploaded by GSSC. The project can be
    precisely retrieved if the projecd ID is specified (via the dx_project_id argument).
    Otherwise, you can supply the dx_project_name argument if you know the name, or use the 
    library_name argument if you know the name of the library that was submitted to GSSC. 
    All sequencing result projects uploaded to DNAnexus by GSSC contain a property named 
    'library_name', and projects will be searched on this property for a matching library name when 
    the library_name argument is specified. If both the library_name and the dx_project_name 
    arguments are specified, only the latter is used in finding a project match. The billing_account 
    argument can optionally be specifed to restrict all project searches to only those that are
    billed to that particular billing account (unless dx_project_id is specified in which case 
    the DNAnexus project is directly retrieved).
    """
    #UHTS = scgpm_lims.Connection()
    #SNYDER_ENCODE_ORG = "org-snyder_encode"
    #LOG_LEVELS = [x for x in logging._levelNames if isinstance(x,str)]
    DX_RAW_DATA_FOLDER = "/raw_data"
    DX_BCL2FASTQ_FOLDER = "/stage0_bcl2fastq"
    DX_SAMPLESHEET_FOLDER  = os.path.join(DX_BCL2FASTQ_FOLDER,"miscellany")
    DX_FASTQ_FOLDER = os.path.join(DX_BCL2FASTQ_FOLDER,"fastqs")
    DX_FASTQC_FOLDER = "/stage1_qc/fastqc_reports"
    DX_QC_REPORT_FOLDER = "/stage2_qc_report"
    #: The extension used for FASTQ files.
    FQEXT = ".fastq.gz"

    def __init__(self,dx_project_id=False,dx_project_name=False,uhts_run_name=False,sequencing_lane=False,library_name=False,billing_account_id=None,latest_project=False):
        """
        Args: 
            dx_project_id - `str`. The ID of the DNAnexus project (i.e. FPg8yJQ900P4ZgzxFZbgJZY2). If specified, no project search 
                will be performed as it will be directly retrieved.
            dx_project_name - `str`. Name of a DNAnexus project containing sequencing results that were 
                uploaded by GSSC.
            uhts_run_name - `str`. Name of the sequencing run in UHTS. This is added as a property to 
                all projects in DNAnexus through the 'seq_run_name' property.
            sequencing_lane - `int`. Lane number of the flowcell on which the library was sequenced. 
                This is in a property named seq_lane_index on all GSSC projects in DNAnexus.
            library_name - `str`. Library name of the sample that was sequenced. This is the name of
                the library that was submitted to GSSC for sequencing, and is added as a property to 
                all GSSC DNAnexus projects via the 'library_name' property.
            billing_account_id - `str`. Name of the DNAnexus billing account that the project belongs to. 
                This will only be used to restrict the search of projects that the user can see to only 
                those billed by the specified account.
            latest_project - `bool`. True indicates that if multiple projects are found given the search
                criteria, the most recently created project will be returned.
        """
        self.dx_project_id = dx_project_id
        self.dx_username = gbsc_dnanexus.utils.get_dx_username()
        self.billing_account_id = billing_account_id
        if self.billing_account_id:
            gbsc_dnanexus.utils.validate_billed_to_prefix(billing_account_id=self.billing_account_id,exception=True)
    
        if not self.billing_account_id:
            self.billing_account_id = None
            #Making sure its set to None in this case, b/c the user could have passed in an empty string,
            # and for this to work is should be set as None from DX's perspective. 
      
        self.dx_project = None
        self.dx_project_name = dx_project_name
        self.uhts_run_name = uhts_run_name
        self.sequencing_lane = sequencing_lane
        self.library_name = library_name
        if not self.dx_project_id and not self.dx_project_name and not self.uhts_run_name and not self.library_name and not self.sequencing_lane:
            raise Exception("You must specify 'dx_project_id', or some combination of 'dx_project_name', 'uhts_run_name', 'library_name', or 'sequencing_lane.")
        self._set_dxproject_id(latest_project=latest_project)
        #_set_dxproject_id sets the following instance attributes:
        # self.dx_project_id
        # self.dx_project_name
        # self.library_name
        if self.dx_project_id:
            self._set_sequencing_run_name() #sets self.sequencing_run_name.

    def _process_dx_project_id(self, dx_project_id):
            if not dx_project_id.startswith("project-"):
                self.dx_project_id = prefix + dx_project_id
  
    def _set_dxproject_id(self,latest_project=False):
        """
        Searches for the project in DNAnexus based on the input arguments when instantiating the class. 
        If multiple projects are found based on the search criteria, an exception will be raised. A 
        few various search strategies are employed, based on the input arguments. In all cases, if the 
        'billing_account_id' was specifed, all searches will search for projects only belonging to the 
        specified billing account. The search strategies work as follows: If the project ID was
        provided, the search will attempt to find the project by ID only. If the project ID wasn't 
        provided, but the project name was specified, then the search will attempt to find the project
        by name and by any project properties that may have been set during instantiation 
        (uhts_run_name, sequencing_lane, and library_name). If neither the project name nor the 
        project ID was specified, then a search by whichever project properties were specified will take place.
    
        This method will not set the self.dx_project_id if none of the search methods are successful 
        in finding a single project, and this may indicate that the sequencing hasn't finished yet.
    
        Args:
            latest_project: `bool`. True indicates that if multiple projects are found given the search 
            criteria, the most recently created project will be returned.
    
        Returns: 
            `str`. The DNAnexus project ID or the empty string if a project wasn't found.
     
        Raises: 
            `scgpm_seqresults_dnanexus.dnanexus_utils.DxMultipleProjectsWithSameLibraryName()`: The 
                search is by self.library_name, and multiple DNAnexus projects have that library name.

            `DxMissingLibraryNameProperty`: The DNAnexus project property 'library_name' is not present. 
        """
        dx_project_props = {}
        if self.library_name:
            dx_project_props["library_name"] = self.library_name
        if self.uhts_run_name:
            dx_project_props["seq_run_name"] = self.uhts_run_name
        if self.sequencing_lane:
            dx_project_props["seq_lane_index"] = str(self.sequencing_lane)
    
        dx_proj = ""
        if self.dx_project_id:
            prefix = "project-"
            if not self.dx_project_id.startswith(prefix):
                self.dx_project_id = prefix + self.dx_project_id
            dx_proj = dxpy.DXProject(dxid=self.dx_project_id)
        elif self.dx_project_name:
            res = dxpy.find_one_project(properties=dx_project_props,billed_to=self.billing_account_id,zero_ok=True,more_ok=False,name=self.dx_project_name)
            if res:
                dx_proj = dxpy.DXProject(dxid=res["id"])
        else:
            #try to find by library_name and potential uhts_run_name
            res = list(dxpy.find_projects(properties=dx_project_props,billed_to=self.billing_account_id))
            if len(res) == 1:
                dx_proj = dxpy.DXProject(dxid=res[0]["id"])
            elif len(res) > 1:
                dx_proj_ids = [x["id"] for x in res]
                if not latest_project:
                    raise DxMultipleProjectsWithSameLibraryName("Error - Multiple DNAnexus projects have the same value for the library_name property value of {library_name}. The projects are {dx_proj_ids}.".format(library_name=self.library_name,dx_proj_ids=dx_proj_ids))
                dx_proj = gbsc_dnanexus.utils.select_newest_project(dx_project_ids=dx_proj_ids)
    
        if not dx_proj:
              return
    
        self.dx_project = dx_proj
        self.dx_project_id = dx_proj.id
        self.dx_project_name = dx_proj.name
        self.dx_project_props = dxpy.api.project_describe(object_id=dx_proj.id,input_params={"fields": {"properties": True}})["properties"]
        try:
            self.library_name = self.dx_project_props["library_name"]
        except KeyError:
            msg = "DNAnexus project {} is missing the library_name property.".format(self.dx_project_name)
            raise DxMissingLibraryNameProperty(msg)

  
    def _set_sequencing_run_name(self):
        """
        Sets the self.sequencing_run_name attribute to the name of the sequencing run in UHTS.
        """
        self.sequencing_run_name = self.dx_project_props["seq_run_name"]
  
    def get_run_details_json(self):
        """
        Retrieves the JSON object for the stats in the file named run_details.json in the project 
        specified by self.dx_project_id.
    
        Returns: 
            JSON object of the run details.
        """
        run_details_filename = "run_details.json"
        run_details_json_id = dxpy.find_one_data_object(more_ok=False,zero_ok=True,project=self.dx_project_id,name=run_details_filename)["id"]
        json_data = json.loads(dxpy.open_dxfile(dxid=run_details_json_id).read())
        #dxpy.download_dxfile(show_progress=True,dxid=run_details_json_id,project=self.dx_project_id,filename=output_name)
        return json_data

    def get_alignment_summary_metrics(self, barcode):
        """
        Parses the metrics in a ${barcode}alignment_summary_metrics file in the DNAnexus project
        (usually in the qc folder). This contains metrics produced by Picard Tools's 
        CollectAlignmentSummaryMetrics program. 
        """
        filename = barcode + ".alignment_summary_metrics"
        # In the call to dxpy.find_one_data_object() below, I'd normally set the 
        # more_ok parameter to False, but this blows-up in Python 3.7 - giving me a RuntimeError. 
        # So, I just won't set it for now. I think dxpy is still mainly a Python 2.7 library and
        # can break in later version of Python3. 
        try:
            file_id = dxpy.find_one_data_object(
                zero_ok=False,
                project=self.dx_project_id,
                name=filename)["id"]
        except dxpy.exceptions.DXSearchError as err:
            msg = "Picard alignment summary metrics for barcode {} in DX project {} not found.".format(barcode, self.dx_project_id)
            debug_logger.error(msg)
            raise DxMissingAlignmentSummaryMetrics(msg)
        fh = StringIO(dxpy.open_dxfile(file_id).read())
        asm = picard.CollectAlignmentSummaryMetrics(fh)
        return asm.metrics
    
    def get_barcode_stats(self, barcode):
        """
        Loads the JSON in a ${barcode}_stats.json file in the DNAnexus project (usually in the qc
        folder). 
        """
        filename = barcode + "_stats.json"
        # In the call to dxpy.find_one_data_object() below, I'd normally set the 
        # more_ok parameter to False, but this blows-up in Python 3.7 - giving me a RuntimeError. 
        # So, I just won't set it for now. I think dxpy is still mainly a Python 2.7 library and
        # can break in later version of Python3. 
        file_id = dxpy.find_one_data_object(
            zero_ok=False,
            project=self.dx_project_id,
            name=filename)["id"]
        json_data = json.loads(dxpy.open_dxfile(file_id).read())
        return json_data
 
    def get_sample_stats_json(self,barcode=None):
        """
        .. deprecated:: 0.1.0
           GSSC has removed the sample_stats.json file since the entire folder it was in has been 
           removed. Use :meth:`get_barcode_stats` instead. 
     
        Retrieves the JSON object for the stats in the file named sample_stats.json in the project 
        specified by self.dx_project_id.  This file is located in the DNAnexus folder stage\d_qc_report.
    
        Args:
            barcode: `str`. The barcode for the sample. Currently, the sample_stats.json file is of the 
                following form when there isn't a genome mapping: 
    
                [{"Sample name": "AGTTCC"}, {"Sample name": "CAGATC"}, {"Sample name": "GCCAAT"}, ...}]. 
    
                When there is a mapping, each dictionary has many more keys in addition to the "Sample name" one.
    
        Returns: 
            `list` of dicts if barcode=None, otherwise a dict for the given barcode.
        """
        sample_stats_json_filename = "sample_stats.json"
        sample_stats_json_id = dxpy.find_one_data_object(more_ok=False,zero_ok=False,project=self.dx_project_id,name=sample_stats_json_filename)["id"]
        #dxpy.download_dxfile(dxid=sample_stats_json_id,project=self.dx_project_id,filename=sample_stats_json_filename)
        json_data = json.loads(dxpy.open_dxfile(sample_stats_json_id).read())
      
        if not barcode:
            return json_data
      
        for d in json_data: #d is a dictionary
            sample_barcode = d["Sample name"]
            if sample_barcode == barcode:
                return d
        if barcode:
            raise DnanexusBarcodeNotFound("Barcode {barcode} for {library_name} not found in {sample_stats_json_filename} in project {project}.".format(barcode=barcode,library_name=self.library_name,sample_stats_json_filename=sample_stats_json_filename,project=self.dx_project_id))
  
    def download_metadata_tar(self,download_dir):  
        """
        Downloads the ${run_name}.metadata.tar file from the DNAnexus sequencing results project.
    
        Args: 
            download_dir: `str` - The local directory path to download the QC report to.
        Returns:
            `str`: The filepath to the downloaded metadata tarball.
        """
        if not os.path.isdir(download_dir):
            os.makedirs(download_dir)  
        res = dxpy.find_one_data_object(project=self.dx_project_id,folder=self.DX_RAW_DATA_FOLDER,name="*metadata.tar",name_mode="glob")
        #res will be something like {u'project': u'project-BzqVkxj08kVZbPXk54X0P2JY', u'id': u'file-BzqVkg800Fb0z4437GXJfGY6'}
        #dxpy.find_one_data_object() raises a dxpy.exceptions.DXSearchError() if nothing is found.
        dx_file = dxpy.DXFile(dxid=res["id"],project=res["project"])
        download_file_name = os.path.join(download_dir,dx_file.name)
        msg = "{filename} to {download_dir}.".format(filename=dx_file.name,download_dir=download_dir)
        debug_logger.debug("Downloading " + msg)
        dxpy.bindings.dxfile_functions.download_dxfile(dxid=dx_file,filename=download_file_name)
        success_logger.info("Downloaded " + msg)
        return download_file_name
  
    def download_run_details_json(self,download_dir):
        """
        Downloads the run_details.json and the barcodes.json from the DNAnexus sequencing results project.
    
        Args: 
            download_dir: `str` - The local directory path to download the QC report to.
    
        Returns:
            `str`. The filepath to the downloaded run_details.json file.
        """
        if not os.path.isdir(download_dir):
            os.makedirs(download_dir)  
        res = dxpy.find_one_data_object(project=self.dx_project_id,folder=self.DX_QC_REPORT_FOLDER,name="run_details.json",name_mode="exact")
        #res will be something like {u'project': u'project-BzqVkxj08kVZbPXk54X0P2JY', u'id': u'file-BzqVkg800Fb0z4437GXJfGY6'}
        #dxpy.find_one_data_object() raises a dxpy.exceptions.DXSearchError() if nothing is found.
        dx_file = dxpy.DXFile(dxid=res["id"],project=res["project"])
        download_file_name = os.path.join(download_dir,dx_file.name)
        msg = "{filename} to {download_dir}.".format(filename=dx_file.name,download_dir=download_dir)
        debug_logger.debug("Downloading " + msg)
        dxpy.bindings.dxfile_functions.download_dxfile(dxid=dx_file,filename=download_file_name)
        success_logger.info("Downloaded " + msg)
        return download_file_name
  
    def download_barcodes_json(self,download_dir):
        """
        Downloads the run_details.json and the barcodes.json from the DNAnexus sequencing results project.
    
        Args:
            download_dir: `str` - The local directory path to download the QC report to.
    
        Returns:
            `str`. The filepath to the downloaded barcodes.json file.
        """
        if not os.path.isdir(download_dir):
            os.makedirs(download_dir)  
        res = dxpy.find_one_data_object(project=self.dx_project_id,folder=self.DX_QC_REPORT_FOLDER,name="barcodes.json",name_mode="exact")
        #res will be something like {u'project': u'project-BzqVkxj08kVZbPXk54X0P2JY', u'id': u'file-BzqVkg800Fb0z4437GXJfGY6'}
        #dxpy.find_one_data_object() raises a dxpy.exceptions.DXSearchError() if nothing is found.
        dx_file = dxpy.DXFile(dxid=res["id"],project=res["project"])
        download_file_name = os.path.join(download_dir,dx_file.name)
        msg = "{filename} to {download_dir}.".format(filename=dx_file.name,download_dir=download_dir)
        debug_logger.debug("Downloading " + msg)
        dxpy.bindings.dxfile_functions.download_dxfile(dxid=dx_file,filename=download_file_name)
        success_logger.info("Downloaded " + msg)
        return download_file_name
  
    def download_samplesheet(self,download_dir):
        """
        Downloads the SampleSheet used in demultiplexing from the DNAnexus sequencing results project.
    
        Args:
            download_dir: `str` - The local directory path to download the QC report to.
    
        Returns:
            `str`. The filepath to the downloaded QC report.
        """
        if not os.path.isdir(download_dir):
            os.makedirs(download_dir)  
        res = dxpy.find_one_data_object(project=self.dx_project_id,folder=self.DX_SAMPLESHEET_FOLDER,name="*_samplesheet.csv",name_mode="glob")
        #res will be something like {u'project': u'project-BzqVkxj08kVZbPXk54X0P2JY', u'id': u'file-BzqVkg800Fb0z4437GXJfGY6'}
        #dxpy.find_one_data_object() raises a dxpy.exceptions.DXSearchError() if nothing is found.
        dx_file = dxpy.DXFile(dxid=res["id"],project=res["project"])
        download_file_name = os.path.join(download_dir,dx_file.name)
        msg = "{filename} to {download_dir}.".format(filename=dx_file.name,download_dir=download_dir)
        debug_logger.debug("Downloading " + msg)
        dxpy.bindings.dxfile_functions.download_dxfile(dxid=dx_file,filename=download_file_name)
        success_logger.info("Downloaded " + msg)
        return download_file_name
  
    def download_qc_report(self,download_dir):
        """
        Downloads the QC report from the DNAnexus sequencing results project.
     
        Args: 
            download_dir: `str` - The local directory path to download the QC report to.
    
        Returns:
            `str`. The filepath to the downloaded QC report.
        """
        if not os.path.isdir(download_dir):
            os.makedirs(download_dir)  
        res = dxpy.find_one_data_object(project=self.dx_project_id,folder=self.DX_QC_REPORT_FOLDER,name="*_QC_Report.pdf",name_mode="glob")
        #res will be something like {u'project': u'project-BzqVkxj08kVZbPXk54X0P2JY', u'id': u'file-BzqVkg800Fb0z4437GXJfGY6'}
        #dxpy.find_one_data_object() raises a dxpy.exceptions.DXSearchError() if nothing is found.
        dx_file = dxpy.DXFile(dxid=res["id"],project=res["project"])
        download_file_name = os.path.join(download_dir,dx_file.name)
        msg = "{filename} to {download_dir}.".format(filename=dx_file.name,download_dir=download_dir)
        debug_logger.debug("Downloading " + msg)
        dxpy.bindings.dxfile_functions.download_dxfile(dxid=dx_file,filename=download_file_name)
        success_logger.info("Downloaded " + msg)
        return download_file_name
  
    def download_fastqc_reports(self,download_dir):
        """
        Downloads the QC report from the DNAnexus sequencing results project.
    
        Args: 
            download_dir: `str` - The local directory path to download the QC report to.
    
        Returns: 
            `str`. The filepath to the downloaded FASTQC reports folder.
        """
        if not os.path.isdir(download_dir):
            os.makedirs(download_dir)  
        msg = "the FASTQC reports to {download_dir}.".format(download_dir=download_dir)
        debug_logger.debug("Downloading " + msg)
        dxpy.download_folder(project=self.dx_project_id,destdir=download_dir,folder=self.DX_FASTQC_FOLDER,overwrite=True)
        success_logger.info("Downloaded " + msg)
        #rename the downloaded folder to ${download_dir}/FASTQC
        return download_dir
  
    def download_project(self,download_dir):
        msg = "Downloading DNAnexus project {proj_name} ({proj_id}).".format(proj_name=self.dx_project_name,proj_id=self.dx_project_id)
        log_success_and_debug(msg)
        if not os.path.isdir(download_dir):
            os.makedirs(download_dir)
        download_dir = os.path.join(download_dir,self.dx_project_name)
        if not os.path.isdir(download_dir):
            os.mkdir(download_dir)
        #download the FASTQC files
        fastqc_dir = os.path.join(download_dir,"FASTQC")
        self.download_fastqc_reports(download_dir=fastqc_dir)
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
        #download the FASTQ files into a FASTQ folder
        log_success_and_debug("Downloading the FASTQ files:")
        fastq_dir = os.path.join(download_dir,"FASTQ")
        dxpy.download_folder(project=self.dx_project_id,destdir=fastq_dir,folder=self.DX_FASTQ_FOLDER,overwrite=False)
        #rename the downloaded folder to ${download_dir}/FASTQ
        open(os.path.join(download_dir,"COPY_COMPLETE.txt"),"w").close()  
      
    
    def download_fastqs(self,dest_dir,barcode,overwrite=False):
        """
        Downloads all FASTQ files in the project that match the specified barcode, or if a barcode 
        isn't given, all FASTQ files as in this case it is assumed that this is not a multiplexed 
        experiment. Files are downloaded to the directory specified by dest_dir. 
    
        Args:
            barcode: `str`. The barcode sequence used. 
            dest_dir: `str`. The local directory in which the FASTQs will be downloaded.
            overwrite: `bool`. If True, then if the file to download already exists in dest_dir, the 
                file will be downloaded again, overwriting it. If False, the file will not be 
                downloaded again from DNAnexus.
    
        Returns: 
             `dict`: The key is the barcode, and the value is a dict with integer keys of 1 for the 
              forward reads file, and 2 for the reverse reads file. If not paired-end, 
    
        Raises:
            `Exception`: The barcode is specified and less than or greater than 2 FASTQ files are found.
        """
        fastq_props = self.get_fastq_files_props(barcode=barcode)
        res = {}  
        for f in fastq_props:
            props = fastq_props[f]
            read_num = int(props["read"])
            barcode = props["barcode"]
            if barcode not in res:
                res[barcode] = {}
            name = props["fastq_file_name"]
            filedest = os.path.abspath(os.path.join(dest_dir,name))
            res[barcode][read_num] = filedest
            if os.path.exists(filedest) and not overwrite:
                continue
            debug_logger.debug("Downloading FASTQ file {name} from DNAnexus project {project} to {path}.".format(name=name,project=self.dx_project_name,path=filedest))
            dxpy.download_dxfile(f,filedest)
        return res
  
    def get_fastq_dxfile_objects(self,barcode=None):
        """
        Retrieves all the FASTQ files in project self.dx_project_name as DXFile objects.
  
        Args:
            barcode: `str`. If set, then only FASTQ file properties for FASTQ files having the specified barcode are returned.
  
        Returns: 
            `list` of DXFile objects representing FASTQ files.
  
        Raises:
            `dnanexus_utils.FastqNotFound`: No FASTQ files were found.
        """
        fq_ext_glob = "*{}".format(self.FQEXT)
        name = fq_ext_glob
        if barcode:
            name = "*_{barcode}_*{FQEXT}".format(barcode=barcode, FQEXT=self.FQEXT)
        fastqs = list(dxpy.find_data_objects(project=self.dx_project_id,folder=self.DX_FASTQ_FOLDER,name=name,name_mode="glob"))
        if not fastqs:
            # Then look for them in all folders:
            fastqs= list(dxpy.find_data_objects(project=self.dx_project_id,name=name,name_mode="glob"))
           
        if not fastqs:
            msg = "No FASTQ files found for run {run} ".format(run=self.dx_project_name)
            if barcode:
                msg += "and barcode {barcode}.".format(barcode=barcode)
            raise FastqNotFound(msg)
        fastqs = [dxpy.DXFile(project=x["project"],dxid=x["id"]) for x in fastqs]
        return fastqs
  
    def get_fastq_files_props(self,barcode=None):
        """
        Returns the DNAnexus file properties for all FASTQ files in the project that match the 
        specified barcode, or all FASTQ files if not barcode is specified.
  
        Args:
            barcode: `str`. If set, then only FASTQ file properties for FASTQ files having the specified barcode are returned.
  
        Returns:
            `dict`. Keys are the FASTQ file DXFile objects; values are the dict of associated properties 
            on DNAnexus on the file. In addition to the properties on the file in DNAnexus, an 
            additional property is added here called 'fastq_file_name'.
  
        Raises:
            dnanexus_utils.FastqNotFound exception if no FASTQ files were found.
        """
        fastqs = self.get_fastq_dxfile_objects(barcode=barcode)   #FastqNotFound Exception here if no FASTQs found for specified barcode.
        dico = {}
        for f in fastqs:
            #props = dxpy.api.file_describe(object_id=f.id, input_params={"fields": {"properties": True}})["properties"]
            props = f.get_properties()
            dico[f] = props
            dico[f]["fastq_file_name"] = f.name
        return dico
