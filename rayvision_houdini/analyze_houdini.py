# -*- coding: utf-8 -*-
"""A interface for maya."""

# Import built-in models
from __future__ import print_function
from __future__ import unicode_literals

import shutil
from builtins import str

import hashlib
import logging
import os
import re
import sys
import time
import traceback
import threading

from rayvision_utils import constants
from rayvision_utils import utils
from rayvision_utils.cmd import Cmd
from rayvision_utils.exception.error_msg import ERROR9899_CGEXE_NOTEXIST
from rayvision_utils.exception.error_msg import ERROR_CGFILE_NOTEXIST
from rayvision_utils.exception.error_msg import VERSION_NOT_MATCH
from rayvision_utils.exception.exception import AnalyseFailError
from rayvision_utils.exception.exception import CGExeNotExistError
from rayvision_utils.exception.exception import CGFileNotExistsError
from rayvision_utils.exception.exception import FileNameContainsChineseError
from rayvision_utils.exception.exception import VersionNotMatchError
from rayvision_houdini.constants import PACKAGE_NAME


if not sys.platform.lower().startswith('lin'):
    try:
        import _winreg
    except ImportError:
        import winreg as _winreg

VERSION = sys.version_info[0]


class AnalyzeHoudini(object):
    """Houdini analyse."""

    def __init__(self, cg_file,
                 software_version,
                 project_name=None,
                 plugin_config=None,
                 render_software="Houdini",
                 local_os=None,
                 workspace=None,
                 custom_exe_path=None,
                 platform="2",
                 custom_db_path=None,
                 logger=None,
                 log_folder=None,
                 log_name=None,
                 log_level="DEBUG"
                 ):
        """Initialize and examine the analysis information.

        Args:
            cg_file (str): Scene file path.
            software_version (str): Software version.
            project_name (str): The project name.
            plugin_config (dict): Plugin information.
            render_software (str): Software name, Houdini by default.
            local_os (str): System name, linux or windows.
            workspace (str): Analysis out of the result file storage path.
            custom_exe_path (str): Customize the exe path for the analysis.
            platform (str): Platform no.
            custom_db_path (str): Custom database file location path.
            logger (object, optional): Custom log object.
            log_folder (str, optional): Custom log save location.
            log_name (str, optional): Custom log file name.
            log_level (string):  Set log level, example: "DEBUG","INFO",
              "WARNING","ERROR".
        """
        self.logger = logger
        self.reg_strings = ["SOFTWARE\\Side Effects Software", "SOFTWARE\\SideFX\\"]
        if not self.logger:
            from rayvision_log.core import init_logger
            init_logger(PACKAGE_NAME, log_folder, log_name)
            self.logger = logging.getLogger(__name__)
            self.logger.setLevel(level=log_level.upper())

        self.check_path(cg_file)
        self.cg_file = cg_file
        self.custom_db_path = custom_db_path

        self.render_software = render_software
        self.software_version = software_version
        self.project_name = project_name
        self.plugin_config = plugin_config if plugin_config else {}

        local_os = self.check_local_os(local_os)
        self.local_os = local_os
        self.tmp_mark = str(int(time.time())) + str(self.get_current_id())
        workspace = os.path.join(self.check_workspace(workspace),
                                 self.tmp_mark)
        if not os.path.exists(workspace):
            os.makedirs(workspace)
        self.workspace = workspace

        if custom_exe_path:
            self.check_path(custom_exe_path)
        self.custom_exe_path = custom_exe_path

        self.platform = platform

        self.task_json = os.path.join(workspace, "task.json")
        self.tips_json = os.path.join(workspace, "tips.json")
        self.asset_json = os.path.join(workspace, "asset.json")
        self.upload_json = os.path.join(workspace, "upload.json")
        self.analyse_success_file = os.path.join(workspace, "analyze_sucess")
        if os.path.exists(self.analyse_success_file):
            shutil.rmtree(self.analyse_success_file)
        self.tips_info = {}
        self.task_info = {}
        self.asset_info = {}
        self.upload_info = {}

        self.check_cg_name()

    @staticmethod
    def get_current_id():
        if isinstance(threading.current_thread(), threading._MainThread):
            return os.getpid()
        else:
            return threading.get_ident()

    @staticmethod
    def check_path(tmp_path):
        """Check if the path exists."""
        if not os.path.exists(tmp_path):
            raise CGFileNotExistsError("{} is not found".format(tmp_path))

    def check_cg_name(self):
        """Check if the scene file name has Chinese.

        Raises:
            FileNameContainsChineseError: Scene file name has Chinese.

        """
        if sys.version_info.major == "3":
            cg_file = self.cg_file
            if utils.check_contain_chinese(cg_file):
                raise FileNameContainsChineseError

    def add_tip(self, code, info):
        """Add error message.

        Args:
            code (str): error code.
            info (str or list): Error message description.

        """
        if isinstance(info, list):
            self.tips_info[code] = info
        else:
            self.tips_info[code] = [info]

    def save_tips(self):
        """Write the error message to tips.json."""
        utils.json_save(self.tips_json, self.tips_info, ensure_ascii=False)

    @staticmethod
    def check_local_os(local_os):
        """Check the system name.

        Args:
            local_os (str): System name.

        Returns:
            str

        """
        if not local_os:
            if "win" in sys.platform.lower():
                local_os = "windows"
            else:
                local_os = "linux"
        return local_os

    def check_workspace(self, workspace):
        """Check the working environment.

        Args:
            workspace (str):  Workspace path.

        Returns:
            str: Workspace path.

        """
        if not workspace:
            if self.local_os == "windows":
                workspace = os.path.join(os.environ["USERPROFILE"],
                                         "renderfarm_sdk")
            else:
                workspace = os.path.join(os.environ["HOME"], "renderfarm_sdk")
        else:
            self.check_path(workspace)

        return workspace

    @staticmethod
    def _win32_regedit(strings):
        return _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, strings)

    @staticmethod
    def _win64_regedit(strings):
        return _winreg.OpenKey(
            _winreg.HKEY_LOCAL_MACHINE, strings, 0,
            (_winreg.KEY_WOW64_64KEY + _winreg.KEY_ALL_ACCESS))

    def _get_all_houdini_ver(self):
        """Get all Houdini versions in the registry.

        Returns (list): All Houdini versions.
        """
        soft_ver = []
        for reg_string in self.reg_strings:
            try:
                self.logger.debug("reg_string %s", reg_string)
                houdini_regedit = self._get_window_regedit(reg_string)
                i = 0
                while 1:
                    name = _winreg.EnumKey(houdini_regedit, i)
                    soft_ver.append(name)
                    i += 1
            except:
                pass
        if "Houdini" in soft_ver:
            soft_ver.remove("Houdini")
        self.logger.debug("soft_ver is : %s", soft_ver)
        return soft_ver

    @staticmethod
    def _match_env(env, string):
        """Get env string.

        Args:
            env (str): Env name.
            string (str): Env val.

        Returns (list): Env names.
        """
        if re.search(" %s " % env.upper(), string):
            return re.findall("set -g %s = '(.*)'" % env.upper(), string)

    def _get_file_save_ver(self):
        """Get the version information in the scene file."""
        max_search_line = 100
        env_filter_list = {"_HIP_SAVEVERSION": ""}
        with open(self.cg_file, 'rb') as file:
            save_num = 0
            for line in file:
                line = utils.str2unicode(line)
                if not line:
                    continue
                if save_num > max_search_line:
                    for env_filter in env_filter_list:
                        if not env_filter_list[env_filter]:
                            self.logger.debug("#warning : not found \"{var}\" in search!\nmaybe you can try to change"
                                              " max line args#".format(var=env_filter))
                            env_filter_list[env_filter] = ""
                    break

                for key in env_filter_list:
                    match = self._match_env(key, line)
                    if match:
                        env_filter_list[key] = match[0]

                full_flag = 1
                for env_filter in env_filter_list:
                    if not env_filter_list[env_filter]:
                        full_flag = 0

                if full_flag:
                    for env_filter in env_filter_list:
                        self.logger.debug('%10s:%s' % (env_filter, env_filter_list[env_filter]))
                    break
                save_num += 1
        return env_filter_list

    @classmethod
    def _get_window_regedit(cls, strings):
        """Get the information in the specified registry path."""
        try:
            return cls._win32_regedit(strings)
        except:
            return cls._win64_regedit(strings)

    def _get_install_path(self, ver):
        """Get the value of InstallPath of the specified registry."""
        location = ""
        if ver:
            for reg_string in self.reg_strings:
                try:
                    reg_path = "%s\\%s" % (reg_string, ver)
                    install_info = self._get_window_regedit(reg_path)
                    location = _winreg.QueryValueEx(install_info, "InstallPath")[0]
                    break
                except:
                    pass
            else:
                location = ""
                self.logger.debug(location)
                raise AnalyseFailError("No registry was added to the Houdini software path")
        else:
            raise AnalyseFailError("Your computer not install Houdini")
        self.save_tips()
        return location

    def compare_the_version(self):
        """Get the program path of Houdini."""
        all_houdini_ver = self._get_all_houdini_ver()
        hip_version_data = self._get_file_save_ver()
        if hip_version_data["_HIP_SAVEVERSION"]:
            file_save_ver = "Houdini {0}".format(hip_version_data["_HIP_SAVEVERSION"])
        else:
            raise AnalyseFailError("'HIP_SAVEVERSION' not found in scene file")

        self.logger.debug("file_save_ver: %s %s", file_save_ver, all_houdini_ver)
        if file_save_ver in all_houdini_ver:
            self.logger.debug("file_save_ver: {}".format(file_save_ver))
            exe_path = self._get_install_path(file_save_ver)
            exe_path = os.path.join(exe_path, "bin", "hython.exe")
        else:
            exe_path = None
        return exe_path, file_save_ver

    def find_location(self):
        """Get the path where the local Houdini startup file is located.

        Raises:
            CGExeNotExistError: The path to the startup file does not exist.

        """
        if self.local_os == "linux":
            exe_path = "/opt/hfs%s/bin/hython" % self.software_version
            num = self.software_version
            if not os.path.isfile(exe_path):
                num = self.software_version[0:2] + ".0"
                exe_path = "/opt/hfs%s/bin/hython" % num
            file_save_ver = "Houdini %s" % num
            self.logger.info("exe_path---%s", exe_path)
        else:
            exe_path, file_save_ver = self.compare_the_version()
        if exe_path is None or not os.path.exists(exe_path):
            raise CGExeNotExistError(ERROR9899_CGEXE_NOTEXIST.format(
                file_save_ver))

        self.logger.info("exe_path: %s", exe_path)
        return exe_path

    def analyse_cg_file(self):
        """Analyse cg file.

        Analyze the scene file to get the path to the startup file of
          the CG software.

        """
        if self.custom_exe_path is not None:
            exe_path = self.custom_exe_path
        else:
            exe_path = self.find_location()
        return exe_path

    def write_task_json(self):
        """Initialize task.json."""
        constants.TASK_INFO["task_info"]["input_cg_file"] = \
            self.cg_file.replace("\\", "/")
        constants.TASK_INFO["task_info"]["project_name"] = self.project_name
        constants.TASK_INFO["task_info"]["cg_id"] = constants.CG_SETTING.get(
            self.render_software.capitalize())
        constants.TASK_INFO["task_info"]["os_name"] = "1" \
            if self.local_os == "windows" else "0"
        constants.TASK_INFO["task_info"]["platform"] = self.platform
        constants.TASK_INFO["software_config"] = {
            "plugins": self.plugin_config,
            "cg_version": self.software_version,
            "cg_name": self.render_software
        }
        utils.json_save(self.task_json, constants.TASK_INFO)

    def check_result(self):
        """Check that the analysis results file exists."""
        for json_path in [self.task_json, self.asset_json,
                          self.tips_json]:
            if not os.path.exists(json_path):
                msg = "Json file is not generated: {0}".format(json_path)
                return False, msg
        return True, None

    @staticmethod
    def get_file_md5(file_path):
        """Generate the md5 values for the scenario."""
        hash_md5 = hashlib.md5()
        if os.path.exists(file_path):
            with open(file_path, 'rb') as file_path_f:
                while True:
                    data_flow = file_path_f.read(8096)
                    if not data_flow:
                        break
                    hash_md5.update(data_flow)
        return hash_md5.hexdigest()

    def write_upload_json(self):
        """Generate the upload.json."""
        assets = self.asset_info["asset"]
        upload_asset = []

        self.upload_info["scene"] = [
            {
                "local": self.cg_file.replace("\\", "/"),
                "server": utils.convert_path(self.cg_file),
                "hash": self.get_file_md5(self.cg_file)
            }
        ]

        for path in assets:
            resources = {}
            local = path.split("  (mtime")[0]
            server = utils.convert_path(local)
            resources["local"] = local.replace("\\", "/")
            resources["server"] = server
            upload_asset.append(resources)

        # Add the cg file to upload.json
        upload_asset.append({
            "local": self.cg_file.replace("\\", "/"),
            "server": utils.convert_path(self.cg_file)
        })

        self.upload_info["asset"] = upload_asset

        utils.json_save(self.upload_json, self.upload_info)

    def get_geo_node_dict(self):
        """Get all render geo node"""
        task_json_dict = utils.json_load(self.task_json)
        geo_node_dict = {}
        scene_info_render = task_json_dict.get('scene_info_render', {})
        if 'geo_node' in scene_info_render:
            for geo_node in scene_info_render.get('geo_node'):
                if geo_node.get('render') == '1':
                    geo_node_dict.update(
                        {geo_node.get('node'): ""}
                    )
        return geo_node_dict

    def set_geo_node_order(self, geo_node_dict):
        """Set geo node dependency.
        
        Args:
            geo_node_dict(dict): all render geo node dict.
        """
        if not geo_node_dict:
            self.logger.error("geo_node_dict is none: {}".format(geo_node_dict))
            return
        sort_list = []
        task_json_dict = utils.json_load(self.task_json)

        scene_info_render = task_json_dict.get('scene_info_render', {})
        task_info_dict = task_json_dict.get('task_info', {})
        sort_list = [int(geo_node_dict[item]) for item in geo_node_dict.keys() if geo_node_dict[item].strip()]
        expect_list = [item for item in range(1, len(geo_node_dict)+1)]
        if (len(sort_list) != len(geo_node_dict)) or (sorted(sort_list) != sorted(expect_list)):
            self.logger.error("Have the wrong sort: {}".format(geo_node_dict))
            return
        for node_dict in scene_info_render['geo_node']:
            if node_dict.get('node') in geo_node_dict.keys():
                node_dict.update(
                    {'geoDependencySort': geo_node_dict[node_dict.get('node')]}
                )
        task_info_dict.update({'multi_node': "0", 'geo_node_dependency': "1"})
        utils.json_save(self.task_json, task_json_dict)
        self.logger.info("geo_node_dict is: {}".format(geo_node_dict))

    def analyse(self, exe_path="", no_upload=False):
        """Build a cmd command to perform an analysis.

        Args:
            exe_path (string): custom rendering software absolute path.
            no_upload (bool): Do you not generate an upload,json file.

        Raises:
            AnalyseFailError: Analysis scenario failed.

        """
        if not os.path.exists(exe_path):
            exe_path = self.analyse_cg_file()
        self.write_task_json()
        script_full_path = os.path.join(os.path.dirname(__file__), "run.py")

        cmd = '"{exe_path}" "{script_full_path}" -file "{cg_file}"' \
              ' -path_json "{json_path}"'.format(
                exe_path=exe_path,
                script_full_path=script_full_path,
                cg_file=self.cg_file,
                json_path=self.workspace
              )

        self.logger.debug(cmd)
        code, _, _ = Cmd.run(cmd, shell=True)
        if not os.path.exists(self.analyse_success_file):
            raise AnalyseFailError("Analyse failed, please check!")

        # Determine whether the analysis is successful by
        #  determining whether a json file is generated.
        status, msg = self.check_result()
        if status is False:
            raise AnalyseFailError(msg)

        self.tips_info = utils.json_load(self.tips_json)
        self.asset_info = utils.json_load(self.asset_json)
        self.task_info = utils.json_load(self.task_json)
        if not no_upload:
            self.write_upload_json()
