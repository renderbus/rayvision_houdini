# -*- coding: utf-8 -*-
"""Houdini render demo."""

from rayvision_api.core import RayvisionAPI
from rayvision_houdini.analyze_houdini import AnalyzeHoudini
from rayvision_sync.upload import RayvisionUpload
from rayvision_sync.download import RayvisionDownload
from rayvision_api.task.check import RayvisionCheck
from rayvision_api.utils import update_task_info, append_to_task, append_to_upload

# API Parameter
render_para = {
    "domain": "task.renderbus.com",
    "platform": "2",
    "access_id": "xxxx",
    "access_key": "xxxx",
}

api = RayvisionAPI(access_id=render_para['access_id'],
                   access_key=render_para['access_key'],
                   domain=render_para['domain'],
                   platform=render_para['platform'])

# Step1：Analyze CG File
analyze_info = {
    "cg_file": r"D:\files\CG FILE\flip_test_slice4.hip",
    "workspace": "c:/workspace",
    "software_version": "17.5.293",
    "project_name": "Project1",
    "plugin_config": {
        'renderman': '22.6'
    }
}
analyze_obj = AnalyzeHoudini(**analyze_info)
analyze_obj.analyse()


# step2: Add some custom parameters, or update the original parameter value
update_task = {
    "pre_frames": "100",
    "stop_after_test": "1"
}
update_task_info(update_task, analyze_obj.task_json)

custom_info_to_task = {
    "env": "houdini_env"
}
append_to_task(custom_info_to_task, analyze_obj.task_json)

custom_info_to_upload = [
    r"D:\files\CG FILE\Shark Test\home_test.build",
    r"C:\workspace\1585303109\task.json"
]
append_to_upload(custom_info_to_upload, analyze_obj.upload_json)


# step3：Check json files
check_obj = RayvisionCheck(api, analyze_obj)
task_id = check_obj.execute(analyze_obj.task_json, analyze_obj.upload_json)


# Step4: Transmission
"""
There are two ways to upload the transmission:
Upload_method: 1: upload four json files and upload the resource file according to upload.json;
               2: json files and resources are uploaded separately;
"""
CONFIG_PATH = {
    "tips_json_path": analyze_obj.tips_json,
    "task_json_path": analyze_obj.task_json,
    "asset_json_path": analyze_obj.asset_json,
    "upload_json_path": analyze_obj.upload_json,
}
upload_obj = RayvisionUpload(api)
"""
The default of the test demo is to upload json and resource files at the same time,
and users can choose their own upload method according to the actual situation.
"""
upload_method = 1
if upload_method == 1:
    # step3.1：Json files are uploaded in conjunction with CG resources
    upload_obj.upload(str(task_id), **CONFIG_PATH)
elif upload_method == 2:
    # step3.2：CG resource files and json are uploaded separately
    upload_obj.upload_asset(upload_json_path=CONFIG_PATH["upload_json_path"])
    upload_obj.upload_config(str(task_id), list(CONFIG_PATH.values()))


# Step5：Submit Task
api.submit(int(task_id))


# Step6：Download
download = RayvisionDownload(api)
# All complete before the automatic start of uniform download.
# download.auto_download_after_task_completed([task_id])
# Poll download (automatic download for each completed frame)
download.auto_download([int(task_id)])