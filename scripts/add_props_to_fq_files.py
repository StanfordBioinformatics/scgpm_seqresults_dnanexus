from argparse import ArgumentParser
import sys
import pdb

import dxpy

PATIENT_ID_PROP_NAME = "lab_patient_id"
PATIENT_GROUP_PROP_NAME = "lab_patient_group"
PATIENT_CONDITION_PROP_NAME = "lab_patient_condition"
dx_projects = ["project-F0bv6b00k49KxZvfGQG3v3qQ","project-F0bxzXj0kgYq5Qzf9jp4fVB0","project-F0bz9GQ0FggyF151x0BQg678","project-F07jGX00P0By6yk2ZkFqVz06","project-F0bJ2bj05gbXG139J83jv49z","project-F0b4Z3002Pf29FK60bqX7bg6"]

fh = open(sys.argv[1])
#read past header
fh.readline()
for line in fh:
	line = line.strip()
	if not line:
		continue
	line = line.split("\t")
	patient_id = line[0].strip()
	patient_group = line[1].strip()
	patient_condition = line[2].strip()
	barcode = line[3].strip()
	for project_id in dx_projects:
		proj = dxpy.DXProject(project_id)
		barcode_glob = "*_{barcode}_*".format(barcode=barcode)
		fastqs = list(dxpy.find_data_objects(project=project_id,folder="/stage0_bcl2fastq/fastqs",name=barcode_glob,name_mode="glob"))
		#each element in fastqs is a dict of the form {u'project': u'project-F0bv6b00k49KxZvfGQG3v3qQ', u'id': u'file-F0bkxbj02f29xYf3q4BvPYJf'}.
		if len(fastqs) != 2:
			raise Exception("Failed to find two FASTQ files for barcode {barcode} in project {project}.".format(barcode=barcode,project=project))
		for f in fastqs:
			props = dxpy.api.file_describe(object_id=f["id"], input_params={"fields": {"properties": True}})["properties"]
			if PATIENT_ID_PROP_NAME not in props:
				props[PATIENT_ID_PROP_NAME] = patient_id
			if PATIENT_GROUP_PROP_NAME not in props:
				props[PATIENT_GROUP_PROP_NAME] = patient_group
			if PATIENT_CONDITION_PROP_NAME not in props:
				props[PATIENT_CONDITION_PROP_NAME] = patient_condition
			print(f)
			dxpy.api.file_set_properties(object_id=f["id"],input_params={"project": f["project"],"properties": props})
			print("Updated properties for file {file_id} in project {project}.".format(file_id=f["id"],project=project_id))
