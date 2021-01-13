# -*- coding: utf-8 -*-
"""A interface for maya."""

# Import built-in models
from __future__ import print_function
from __future__ import unicode_literals

import hashlib
import logging
import os
import traceback

import re
import sys
import time
from builtins import str

from rayvision_utils import constants
from rayvision_utils import utils
from rayvision_utils.cmd import Cmd
from rayvision_utils.exception import tips_code
from rayvision_utils.exception.error_msg import ERROR9899_CGEXE_NOTEXIST
from rayvision_utils.exception.error_msg import ERROR_CGFILE_NOTEXIST
from rayvision_utils.exception.error_msg import VERSION_NOT_MATCH
from rayvision_utils.exception.exception import AnalyseFailError
from rayvision_utils.exception.exception import CGExeNotExistError
from rayvision_utils.exception.exception import CGFileNotExistsError
from rayvision_utils.exception.exception import FileNameContainsChineseError
from rayvision_utils.exception.exception import VersionNotMatchError

if not sys.platform.lower().startswith('lin'):
    try:
        import _winreg
    except ImportError:
        import winreg as _winreg

VERSION = sys.version_info[0]


class AnalyzeHoudini(object):
    def __init__(self, cg_file, software_version, project_name=None,
                 plugin_config=None, render_software="Houdini",
                 local_os=None, workspace=None, custom_exe_path=None,
                 platform="2", custom_db_path=None):
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

        """
        self.logger = logging.getLogger(__name__)

        self.check_path(cg_file)
        self.cg_file = cg_file
        self.custom_db_path = custom_db_path

        self.render_software = render_software
        self.software_version = software_version
        self.project_name = project_name
        self.plugin_config = plugin_config

        local_os = self.check_local_os(local_os)
        self.local_os = local_os
        self.tmp_mark = str(int(time.time()))
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
        self.tips_info = {}
        self.task_info = {}
        self.asset_info = {}
        self.upload_info = {}

        self.check_cg_name()

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
                self.add_tip(tips_code.CONTAIN_CHINESE, cg_file)
                self.save_tips()
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

    def get_save_version(self, cg_file):
        """Check the CG version of the scene file .

        Args:
            cg_file (str): Scene file path.

        Returns:
            str: Create a CG software version of the scene file.
                e.g.:
                    "17.0.352".

        """
        if os.path.exists(cg_file):
            with open(cg_file, "rb") as hipf:
                not_find = True
                search_elm = 2
                search_elm_cunt = 0
                while not_find:
                    line = str(hipf.readline()).encode("utf-8")
                    if "set -g _HIP_SAVEVERSION = " in str(line):
                        pattern = re.compile(r"\d+\.\d+\.\d+\.?\d+")
                        _HV = pattern.findall(str(line))
                        _hfs_save_version = _HV[0]
                        search_elm_cunt += 1

                    # The $HIP val with this file saved
                    if "set -g HIP = " in str(line):
                        pattern = (re.compile("\\'.*\\'")
                                   if sys.version[:1] == "2" else
                                   re.compile(r"\\'.*\\'"))
                        _Hip = pattern.search(str(line)).group()
                        _hip_save_val = _Hip.split("\'")[1].replace("\\", "/")
                        search_elm_cunt += 1
                    if search_elm_cunt >= search_elm:
                        not_find = False
        else:
            self.add_tip(tips_code.CGFILE_NOTEXISTS, cg_file)
            self.save_tips()
            raise CGFileNotExistsError(ERROR_CGFILE_NOTEXIST.format(
                cg_file))
        self.logger.info("_hfs_save_version---%s" % _hfs_save_version)
        return _hfs_save_version

    def _get_install_path(self, version):
        location = None
        version_str = "{0} {1}".format(self.render_software, version)
        string = r'SOFTWARE\Side Effects Software\{0}'.format(version_str)
        self.logger.debug(string)
        try:
            handle = self._win_regedit(string)
            location, type = _winreg.QueryValueEx(handle, "InstallPath")
            self.logger.debug("{0} {1}".format(location, type))

        except (WindowsError, FileNotFoundError):
            msg = traceback.format_exc()
            self.logger.error(msg)

        return location

    @classmethod
    def _win_regedit(cls, strings):
        try:
            return cls._win32_regedit(strings)
        except Exception:
            try:
                return cls._win64_regedit(strings)
            except Exception:
                try:
                    cls._win64_regedit("SOFTWARE")
                except Exception as e:
                    traceback.format_exc()
                    raise e

    @staticmethod
    def _win32_regedit(strings):
        return _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, strings)

    @staticmethod
    def _win64_regedit(strings):
        return _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, strings, 0,
                               (_winreg.KEY_WOW64_64KEY + _winreg.KEY_ALL_ACCESS))

    def location_from_reg(self, version):
        """Get the software installation path from the registry.
        When the smaller version does not match, it looks for the larger version,
        If the larger version does not match, it throws an error

        Args:
            version (str): CG software version.

        Returns (str): CG software absolute path.

        """
        version_list = []
        try:
            handle = self._win_regedit(r'SOFTWARE\Side Effects Software')
            i = 0
            while 1:
                name = _winreg.EnumKey(handle, i)
                self.logger.debug("{}".format(name))
                version_list.append(name)
                i += 1
        except OSError:
            logging.debug("User local houdini software versions===> %s" % version_list)
        try:
            if len(version_list):
                folder_name = "Houdini {}".format(version)
                if folder_name not in version_list:
                    s_ver = folder_name.split(".", maxsplit=2)
                    b_ver = s_ver[0] + "." + s_ver[1]
                    for ver in version_list:
                        if b_ver in ver:
                            b_version = ver.split(" ")[-1]
                            self.logger.info("Match large version===>", b_version)
                            return self._get_install_path(b_version)

                    error_msg = "Your houdini Software version is not any match"
                    self.logger.error("{}: {}".format(error_msg, version))
                    self.add_tip(tips_code.CG_NOTMATCH, error_msg)
                    self.save_tips()
                    raise VersionNotMatchError(VERSION_NOT_MATCH.format(version))
                else:
                    return self._get_install_path(version)
            else:
                error_msg = "Cannot found any houdini version"
                self.logger.error("{}: {}".format(error_msg, version))
                if version != "":
                    self.add_tip(tips_code.CG_NOTEXISTS, error_msg)
                    self.save_tips()
                    raise CGExeNotExistError(ERROR9899_CGEXE_NOTEXIST.format(version))
        except Exception as e:
            traceback.format_exc()
            raise e

    def find_location(self):
        """Get the path where the local Houdini startup file is located.

        Raises:
            CGExeNotExistError: The path to the startup file does not exist.

        """
        exe_path = None
        if self.local_os == "linux":
            exe_path = "/opt/hfs%s/bin/hython-bin" % self.software_version
            if not os.path.isfile(exe_path):
                num = self.software_version[0:2] + ".0"
                exe_path = "/opt/hfs%s/bin/hython-bin" % num
            self.logger.info("exe_path---%s" % exe_path)
        else:
            location = self.location_from_reg(self.software_version)
            tmp_exe_path = os.path.join(location, "bin", "hython.exe")
            if os.path.exists(tmp_exe_path):
                exe_path = tmp_exe_path

        if exe_path is None:
            error_msg = "Software of scene has not been found"
            self.add_tip(tips_code.CG_NOTEXISTS, error_msg)
            self.save_tips()
            raise CGExeNotExistError(ERROR9899_CGEXE_NOTEXIST.format(
                self.render_software))

        self.logger.info("exe_path: %s", exe_path)
        return exe_path

    def analyse_cg_file(self):
        """ analyse cg file.

        Analyze the scene file to get the path to the startup file of the CG
        software.

        """
        # Find the version from the cg file
        version = self.get_save_version(self.cg_file)
        self.logger.info("version: %s", version)

        if version != self.software_version:
            self.add_tip(tips_code.CG_NOTMATCH, "{0} {1}".format(
                self.render_software, self.software_version))
            self.save_tips()

        if self.custom_exe_path is not None:
            exe_path = self.custom_exe_path
        else:
            exe_path = self.find_location()
        return exe_path

    def write_task_json(self):
        """The initialization task.json."""
        constants.TASK_INFO["task_info"]["input_cg_file"] = self.cg_file.replace("\\", "/")
        constants.TASK_INFO["task_info"]["project_name"] = self.project_name
        constants.TASK_INFO["task_info"]["cg_id"] = constants.CG_SETTING.get(self.render_software.capitalize())
        constants.TASK_INFO["task_info"]["os_name"] = "1" if self.local_os == "windows" else "0"
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

    def get_file_md5(self, file_path):
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


    def analyse(self, exe_path=""):
        """Build a cmd command to perform an analysis.

        Args:
            exe_path (string): custom rendering software absolute path.

        Raises:
            AnalyseFailError: Analysis scenario failed.

        """
        if not os.path.exists(exe_path):
            exe_path = self.analyse_cg_file()
        self.write_task_json()
        script_full_path = os.path.join(os.path.dirname(__file__), "run.py")

        cmd = '"{exe_path}" "{script_full_path}" -file "{cg_file}" -path_json "{json_path}"'.format(
            exe_path=exe_path,
            script_full_path=script_full_path,
            cg_file=self.cg_file,
            json_path=self.workspace
        )

        self.logger.debug(cmd)
        code, _, _ = Cmd.run(cmd, shell=True)
        if code != 0:
            self.add_tip(tips_code.UNKNOW_ERR, "")
            self.save_tips()
            raise AnalyseFailError

        # Determine whether the analysis is successful by
        #  determining whether a json file is generated.
        status, msg = self.check_result()
        if status is False:
            self.add_tip(tips_code.UNKNOW_ERR, msg)
            self.save_tips()
            raise AnalyseFailError(msg)

        return self
