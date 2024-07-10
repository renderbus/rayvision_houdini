# -*- coding:UTF-8 -*-
"""Run analyse file."""

import os
import sys

current_file = os.path.normpath(os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, current_file)
import hanalyse

args = sys.argv
if "-file" in args:
    cg_file_flag = args.index("-file")
    hip_file = args[cg_file_flag + 1]
    print("hip_file: " + hip_file)
if "-path_json" in args:
    path_json_flag = args.index("-path_json")
    path_json = args[path_json_flag + 1]
    print("path_json: " + path_json)
if "-getaset" in args:
    getaset_flag = args.index("-getaset")
    getaset = args[getaset_flag + 1]
    print("getaset: " + getaset)
else:
    getaset = "0"
param_dict = {
    "hip_file": hip_file,
    "path_json": path_json,
    "getaset": getaset
}

hanalyse.AnalysisAssets(param_dict).doit()
