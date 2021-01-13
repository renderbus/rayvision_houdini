# -*- coding: utf-8 -*-
"""only analyze houdini"""

from rayvision_houdini.analyze_houdini import AnalyzeHoudini

analyze_info = {
    "cg_file": r"D:\files\CG FILE\flip_test_slice4.hip",
    "workspace": "c:/workspace",
    "software_version": "17.5.293",
    "project_name": "Project1",
    "plugin_config": {
        'renderman': '22.6'
    }
}

AnalyzeHoudini(**analyze_info).analyse(exe_path="C:\Program Files\Side Effects Software\Houdini 17.0.506\bin\hython.exe")