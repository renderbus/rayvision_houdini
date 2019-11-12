.. warning::
   请确保本地python环境能够正常使用，并已经安装 `rayvision_api <https://pip.renderbus.com/simple/rayvision-api/>`_ 、`rayvision_utils <https://pip.renderbus.com/simple/rayvision-utils/>`_ 、`rayvision_sync <https://pip.renderbus.com/simple/rayvision-sync/>`_ 模块。

Houdini介绍和使用
.............................

**rayvision_houdini** 主要是进行调用Houdini渲染服务器进行CG渲染的模组，
渲染流程会依赖 `rayvision_api <https://pip.renderbus.com/simple/rayvision-api/>`_ 、`rayvision_utils <https://pip.renderbus.com/simple/rayvision-utils/>`_ 、`rayvision_sync <https://pip.renderbus.com/simple/rayvision-sync/>`_ 模块.


houdini演示demo
----------------

学习的最好方法就是参考例子，`rayvision_houdini <https://pip.renderbus.com/simple/rayvision-houdini/>`_ 也不例外，我们也提供了下面的一个使用 **demo** 样例供您参考::

    from __future__ import print_function
    from rayvision_api.core import RayvisionAPI
    from rayvision_utils.analyse_handle import RayvisionAnalyse
    from rayvision_api.task.handle import RayvisionTask
    from rayvision_api.task.check import RayvisionCheck
    from rayvision_sync.transfer import RayvisionTransfer
    from rayvision_sync.upload import RayvisionUpload
    from rayvision_sync.manage import RayvisionManageTask
    from rayvision_sync.download import RayvisionDownload

    # Set necessary parameters

    user_info = {
        "domain_name": "task.renderbus.com",  # 用戶不需要修改
        "platform": "2",  # 平台号
        "access_id": "K2lbvJSlPScStv72niHGXZtbQYc5F6hkj",  # 用户自行修改(必填)
        "access_key": "6b4b6eab841772113113b61c79db68d85",  # 用户自行修改(必填)
        "local_os": 'windows',
        "workspace": "c:/workspace",  # 本地保存根目录自动创建(用户可自行修改,全英文路径)
    }

    render_config = {
        "render_software": "Houdini",  # CG软件（Maya, Houdini, Katana, Clarisse）
        "software_version": "17.5.293",  # 注意CG版本的形式
        "project_name": "Project1",
        "plugin_config": {}  # CG插件，无插件则为{}
    }

    # CG资源文件绝对路径(必须)
    cg_file = r"E:\copy\rman225Test_03.hip"

    api = RayvisionAPI(access_id=user_info['access_id'],
                       access_key=user_info['access_key'],
                       domain=user_info['domain_name'],
                       platform=user_info['platform'])

    # 打印当前用户信息
    print(api.user.query_user_profile())

    # Rayvision analysis
    task = RayvisionTask(user_info, render_config, cg_file)
    RayvisionAnalyse.execute(task)
    RayvisionCheck(task).execute(task.task_info, task.upload_info)

    # Upload json file
    transfer_info = {
        'config_bid': api.user_info['config_bid'],
        'input_bid': api.user_info['input_bid'],
        "domain_name": user_info['domain_name'],
        "platform": user_info['platform'],
        "local_os": user_info['local_os'],
        "user_id": api.user_info['user_id']
    }
    config_path = [
        task.task_json_path,
        task.tips_json_path,
        task.asset_json_path,
        task.upload_json_path,
    ]

    # start transfer(传输)
    TRANS = RayvisionTransfer(transfer_info)
    UPLOAD = RayvisionUpload(TRANS)
    UPLOAD.upload(task.task_id, config_path, task.upload_json_path)

    task_id = int(task.task_id)
    result = api.submit(task_id)

    # download(下载)
    manage_task = RayvisionManageTask(api)
    TRANS.manage_task = manage_task
    TRANS.user_info["output_bid"] = api.user_info["output_bid"]
    TRANS.user_info["local_path"] = r"C:\workspace"  # 下载资源本地保存路径（用户可自行修改）
    download = RayvisionDownload(TRANS)

    # demo提供2种下载方式用户自行选择
    # download.auto_download_after_task_completed([task_id])  # 所有都完成后才自动开始统一下载
    download.auto_download([task_id])  # 轮询下载（每完成每一帧自动下载）

Demo相关参数
-----------

.. list-table:: user_info
   :widths: 15 10 30
   :header-rows: 1

   * - 参数名
     - 参数值
     - 描述
   * - domain_name
     - task.renderbus.com
     - 渲染接口URL
   * - platform
     - 2
     - 平台号ID值
   * - access_id
     - K2lbvJSlPScStv72niHGXZtbQYc5F6hkj
     - 用户开发者中心AccessID（非user_id）
   * - access_key
     - 6b4b6eab841772113113b61c79db68d85
     - 用户开发者中心AccessKey
   * - local_os
     - windows
     - 用户使用系统（window / linux）
   * - workspace
     - c:/workspace
     - 本地文档保存目录（下载目录可自行设置）


.. list-table:: render_config
   :widths: 15 10 30
   :header-rows: 1

   * - 参数名
     - 参数值
     - 描述
   * - render_software
     - Houdini
     - CG软件名(注意首字母大写)
   * - software_version
     - 17.5.293
     - CG软件版本
   * - project_name
     - project1
     - 自定义项目名(可为空)
   * - plugin_config
     - {}
     - CG所用插件(可为空)