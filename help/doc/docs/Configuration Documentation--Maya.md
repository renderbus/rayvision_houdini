Maya configuration profile
======

> Analysis: We analyze the information that needed in the scene and save it to task.json, asset.json, upload.json, tips.json for further analysis and processing.
    
    
### 1.task.json analysis


> Description: Store scene analysis results, rendering settings, etc.


**task.json example**


```json
{
    "scene_info_render": {
        "defaultRenderLayer": {
            "renderable": "1", 
            "env": {}, 
            "is_default_camera": "1", 
            "option": "", 
            "common": {
                "image_format": "exr", 
                "end": "10", 
                "width": "960", 
                "image_file_prefix": "", 
                "all_camera": [
                    "stereoCameraRightShape", 
                    "stereoCameraLeftShape", 
                    "stereoCameraCenterCamShape", 
                    "perspShape", 
                    "cameraShape2", 
                    "cameraShape1"
                ], 
                "render_camera": [
                    "cameraShape1"
                ], 
                "start": "1", 
                "animation": "False", 
                "renderer": "mentalRay", 
                "frames": "1-10[1]", 
                "height": "540", 
                "renumber_frames": "False", 
                "by_frame": "1"
            }
        }, 
        "mut": {
            "renderable": "1", 
            "is_default_camera": "1", 
            "option": "", 
            "common": {
                "image_format": "exr", 
                "end": "10", 
                "width": "960", 
                "image_file_prefix": "", 
                "all_camera": [
                    "stereoCameraRightShape", 
                    "stereoCameraLeftShape", 
                    "stereoCameraCenterCamShape", 
                    "perspShape", 
                    "cameraShape2", 
                    "cameraShape1"
                ], 
                "render_camera": [
                    "cameraShape1", 
                    "stereoCameraLeftShape"
                ], 
                "start": "1", 
                "animation": "False", 
                "renderer": "mentalRay", 
                "frames": "1-10[1]", 
                "height": "540", 
                "renumber_frames": "False", 
                "by_frame": "1"
            }
        }
    }, 
    "task_info": {
        "is_layer_rendering": "1", 
        "cg_id": "2000", 
        "ram": "64", 
        "os_name": "1", 
        "render_layer_type": "0", 
        "is_distribute_render": "0", 
        "input_cg_file": "D:/chensr/scene/maya2016_multi_layers_cameras.ma", 
        "job_stop_time": "28800", 
        "user_id": "10000031", 
        "pre_frames": "000", 
        "platform": "2", 
        "is_picture": "0", 
        "project_id": "3316", 
        "channel": "4", 
        "tiles_type": "block", 
        "tiles": "1", 
        "project_name": "dasdd", 
        "distribute_render_node": "3", 
        "frames_per_task": "1", 
        "stop_after_test": "2", 
        "input_project_path": "", 
        "task_id": "439800", 
        "task_stop_time": "86400", 
        "time_out": "12"
    }, 
    "software_config": {
        "cg_version": "2016", 
        "cg_name": "Maya", 
        "plugins": {}
    }
}
```


**task.json parameter analysis**


Parameters | Type | Description | Examples
---|---|---|---
software_config | object | rendering environment (software type, version, and plugins used, etc.) | [see software_config object](#software_config)
task_info | object | Rendering settings (priority frame, number of rendered frames, timeout, etc.) | [see task_info object](#task_info)
scene_info_render | object | Analysis result of the scene (render nodes, output paths, etc. in the scene) | [see scene_info_render object](#scene_info_render)


**<span id="software_config">software_config object analysis</span>**


Parameters | Type | Description | Examples
---|---|---|---
cg_name | string | Software Name | "Maya"
cg_version | string | Software Version | "2016"
plugins | object | plugin object. <br>key is the plugin name, value is the plugin version | {}


**<span id="task_info">task_info object analysis</span>**


Parameters | Type | Description | Examples
---|---|---|---
is_layer_rendering | string | Whether maya enables layered rendering.<br/>"0":Close<br/>"1":On<br/> | "1"
cg_id | string | Render software id."2016": Katana | "2016"
ram | string | Rendering machine memory requirements. 64/128 GB| "64"
os_name | string | Rendering operating system, "0":Linux; "1": Windows | "0"
render_layer_type | string | Render layer mode. <br/>"0": renderlayer<br/>"1": rendersetup | "0"
is_distribute_render | string | Whether to enable distributed rendering. <br/>"0":Close<br/>"1":On | "0"
input_cg_file | string | Render scene local path | 
job_stop_time | string | Minor task stops due to timeout, unit: second | "28800"
user_id | string | User id | 
pre_frames | string | Priority rendering | "000:1,3-4[1]" means: <br/>Priority rendering of the first frame: No<br/>Priority rendering of the middle frame: No<br/>Priority rendering of the last frame: No<br/>Priority rendering of the custome frame: 1,3-4[1]
platform | string | Submit platform | "2"
is_picture | string | Is picture | "0"
project_id | string | Project id | 
channel | string | Submission channel. "4":API/SDK | "4"
tiles_type | string | block/strip | "block"
tiles | string | The number of blocks, greater than 1 is divided into blocks or strips, equal to 1 is a single machine | "1"
project_name | string | Project name | "test"
distribute_render_node | string | Distributed rendering machine number | "3"
frames_per_task | string | The quantity of the frames that rendered in one machine| "1"
stop_after_test | string | Whether to pause the task after the priority rendering is completed <br/>"1":Pause the task after the priority rendering is completed<br/>"2". Do not pause the task after the priority rendering is completed.
input_project_path | string | Project path, such as user does not set a null string passing| 
task_id | string | Task id | 
task_stop_time | string | major task stops due to timeout  unit: second | "86400"
time_out | string | Timeout period unit:hour | "12"


**<span id="scene_info_render">scene_info_render object analysis</span>**


Parameters | Type | Description | Examples
---|---|---|---
layer | object | layer information | [See scene_info_render.layer object](#scene_info_render.layer)


**<span id="scene_info_render.layer">scene_info_render.layer object</span>**


Parameters | Type | Description | Examples
---|---|---|---
renderable | string | renderable | "1"
env | object |  | {}
is_default_camera | string | Whether to use the default camera, the default is "1" | "1" 
option | string | Renderer information | ""
common | object | Scene common information | [See scene_info_render.layer.common object](#scene_info_render.layer.common)


**<span id="scene_info_render.layer.common">scene_info_render.layer.common object</span>**


Parameters | Type | Description | Examples
---|---|---|---
image_format | string | image format | "jpg"
end | string | end frame | "100"
width | string | Resolution-width | "1920"
image_file_prefix | string | image file prefix, "<RenderLayer>/<Scence>" | ""
all_camera | array<string> | all camera list | ["stereoCameraRightShape", "cameraShape1"]
render_camera | array<string> | renderable camera list | ["stereoCameraRightShape"]
start | string | start frame | "1"
animation | string | Animation switch | "1"
renderer | string | Renderer name | “arnold“
frames | string | frames | "1-10[1]"
height | string | Resolution-height | "1080"
renumber_frames | string | renumber frames | "1"
by_frame | string | Frame interval | "1"


### 2.upload.json analysis


> Description: Stores the asset path information that needs to be uploaded.


**upload.json example**
```json
{
  "asset": [
    {
      "local": "D:/chensr/scene/maya2016_multi_layers_cameras.ma", 
      "server": "/D/chensr/scene/maya2016_multi_layers_cameras.ma"
    }
  ]
}
```


**upload.json parameter analysis**


Parameters | Type | Description | Examples
---|---|---|---
asset | object | The asset path information that needed to be uploaded | [See asset object analysis](#asset)


**<span id="asset">asset object analysis</span>**


Parameters | Type | Description | Examples
---|---|---|---
local | string | Asset Local Path | "D:/chensr/scene/maya2016_multi_layers_cameras.ma"
server | string | Server-side relative path, generally consistent with local path | "/D/chensr/scene/maya2016_multi_layers_cameras.ma"


### 3.tips.json analysis


> Description: Stores the analyzed errors and warnings


```json
{}
```
