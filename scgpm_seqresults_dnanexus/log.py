# -*- coding: utf-8 -*-                                                                                 
                                                                                                        
###                                                                                                     
# © 2018 The Board of Trustees of the Leland Stanford Junior University                                 
# Nathaniel Watson                                                                                      
# nathankw@stanford.edu                                                                                 
### 

import os
import logging

import scgpm_seqresults_dnanexus as sd

def get_logfile_name(tags):
  """Formulates a log file name that incorporates the provided tags.

  The log file will be located in ``scgpm_seqresults_dnanexus.LOG_DIR``.
  
  Args:
      tags: `list` of tags to append to the log file name. Each tag will be '_' delimited. Each tag
          will be added in the same order as provided.
  """
  if not os.path.exists(sd.LOG_DIR):
    os.mkdir(sd.LOG_DIR)
  filename = "log"
  for tag in tags:
    filename += "_{}".format(tag)
  filename += ".txt"
  filename = os.path.join(sd.LOG_DIR,filename)
  return filename

def add_file_handler(logger,level,tags):
  """Creates and Adds a file handler (`logging.FileHandler` instance) to the specified logger. 

  Args:
      logger: The `logging.Logger` instance to add the new file handler to.
      level: `str`. The logging level for which the handler accepts messages, i.e. `logging.INFO`.
      tags: `list` of tags to append to the log file name. Each tag will be '_' delimited. Each tag
           will be added in the same order as provided.
  """
  f_formatter = logging.Formatter('%(asctime)s:%(name)s:\t%(message)s')
  filename = get_logfile_name(tags)
  handler = logging.FileHandler(filename=filename,mode="a")
  handler.setLevel(level)
  handler.setFormatter(f_formatter)
  logger.addHandler(handler)
