#!/usr/bin/env python3

"""
Writes a tab-delimited file containg information about all projects in DNAnexus that are billed to
the specified org. The field names are:

      Name,
      ID,
      library_name,
      seq_run_name,
      lab,
      paired_end,
      sequencer_type,
      seq_instrument,
      seq_lane_index,
      queue,
      experiment_type

"""

import argparse

import dxpy

import gbsc_dnanexus.utils 

def get_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-o", "--outfile", required=True, help="The output file.")
    parser.add_argument("--org", required=True, help="The DNAnexus org in which the projects belong.")
    return parser

def main():
    parser = get_parser()
    args = parser.parse_args()
    org = gbsc_dnanexus.utils.add_dx_orgprefix(args.org)
    outfile = args.outfile
    fout = open(outfile, "w")

    projects = dxpy.api.org_find_projects(object_id=org)["results"]
    print("There are", len(projects), "projects.")
    header = [
        "Name",
        "ID",
        "library_name",
        "seq_run_name",
        "lab",
        "paired_end",
        "sequencer_type",
        "seq_instrument",
        "seq_lane_index",
        "queue",
        "experiment_type"
    ]
    fout.write("\t".join(header) + "\n")
    for p in projects:
        proj = dxpy.DXProject(dxid=p["id"])
        print(proj.name)
        fout.write(proj.name + "\t" + proj.id)
        props = proj.describe(input_params={"properties": True})["properties"] 
        fout.write("\t" + props.get("library_name", ""))
        fout.write("\t" + props.get("seq_run_name", ""))
        fout.write("\t" + props.get("lab", ""))
        fout.write("\t" + props.get("paired_end", ""))
        fout.write("\t" + props.get("sequencer_type", ""))
        fout.write("\t" + props.get("seq_instrument", ""))
        fout.write("\t" + props.get("seq_lane_index", ""))
        fout.write("\t" + props.get("queue", ""))
        fout.write("\t" + props.get("experiment_type", ""))
        fout.write("\n")

    fout.close()
    

if __name__ == "__main__":
    main()
