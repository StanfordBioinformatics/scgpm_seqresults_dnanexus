#!/bin/bash -eu

###
# © 2018 The Board of Trustees of the Leland Stanford Junior University
# Nathaniel Watson
# nathankw@stanford.edu
#2016-11-17
###

set -o pipefail

###CONFIG###
dx_user_name=
output_dir=
logfile=
###########

function help {
  echo "howdy"
}

infile=

help() {
  echo "Wrapper for download_project.py in the git@github.com:StanfordBioinformatics/scgpm_seqresults_dnanexus.git repository."
  echo "In the CONFIG section near the top of this script, enter values for the variables dx_user_name, output_dir, and logfile."
  echo "This wrapper is thus useful for standardizing the values of the aforementioned variables, for standardized worfklows."
  echo
  echo "Required args:"
  echo " -i The input file containing DNAnexus project IDs, one per line."
}

while getopts "i:h" opt
do
  case $opt in
    i) infile=${OPTARG}
       ;;
    h) help
       exit
       ;;
  esac
done

if [[ ${#@} -eq 0 ]]
then
  help
fi

while read dx_proj_id
do
  if [[ ${dx_proj_id} =~ ^# ]]
  then
    continue
  fi

  lab=$(dx describe ${dx_proj_id} --verbose --json | jq .properties.lab)

  lab_dir=${output_dir}/${lab}
  if ![[ -d ${lab_dir} ]]
  then
    mkdir ${lab_dir}
  fi

  download_project.py -u ${dx_user_name} --download-dir ${lab_dir} --dx-project-id ${dx_proj_id} -l ${logfile}
  if [[ $? -ne 0 ]]
  then
    echo "Error downloading ${dx_proj_id}"
    exit
  fi
done < ${infile}
