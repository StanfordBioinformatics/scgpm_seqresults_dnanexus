# -*- coding: utf-8 -*-

###
# © 2018 The Board of Trustees of the Leland Stanford Junior University
# Nathaniel Watson
# nathankw@stanford.edu
###

"""Utilities for working with the SCGPM Sequencing Center application logic on DNAnexus.
"""

import sys
import logging

import scgpm_seqresults_dnanexus.log as sd_log

#: The directory that contains log files.
LOG_DIR = "Logs_scgpm_seqresults_dnanexus"

#: A ``logging.Logger`` instance that logs all messages sent to it to STDOUT, as well as
#: a log file in the folder specified by ``LOG_DIR``. In addition, another file handler
#: is created that accepts messages at the level ``logging.ERROR``, and lives in the same folder.
debug_logger = logging.getLogger(__name__)
level = logging.DEBUG
debug_logger.setLevel(level)
sd_log.add_file_handler(logger=debug_logger,level=level,tags=["debug"])
sd_log.add_file_handler(logger=debug_logger,level=logging.ERROR,tags=["error"])
f_formatter = logging.Formatter('%(asctime)s:%(name)s:\t%(message)s')
ch = logging.StreamHandler(stream=sys.stdout)
ch.setLevel(level)
ch.setFormatter(f_formatter)
debug_logger.addHandler(ch)
