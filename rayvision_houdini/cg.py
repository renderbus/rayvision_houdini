"""A interface for cg."""

from __future__ import unicode_literals
from __future__ import print_function
import os
import re
import sys
import traceback

# Import local models
from rayvision_utils.json_handle import JsonHandle
from rayvision_utils import utils
from rayvision_utils.exception import tips_code
from rayvision_utils.exception.exception import FileNameContainsChineseError
from rayvision_utils.exception.exception import CGExeNotExistError
from rayvision_utils.exception.exception import CGFileNotExistsError
from rayvision_utils.exception.exception import VersionNotMatchError
from rayvision_utils.exception.exception import AnalyseFailError
from rayvision_utils.exception.error_msg import VERSION_NOT_MATCH
from rayvision_utils.exception.error_msg import ERROR9899_CGEXE_NOTEXIST
from rayvision_utils.exception.error_msg import ERROR_CGFILE_NOTEXIST

if not sys.platform.startswith('lin'):
    try:
        import _winreg
    except ImportError:
        import winreg as _winreg

VERSION = sys.version_info[0]


class Houdini(JsonHandle):
    """
    Houdini
    """

    def __init__(self, *args, **kwargs):
        super(Houdini, self).__init__(*args, **kwargs)
        if sys.platform.startswith("lin"):
            self.linux_platform = True
        else:
            self.linux_platform = False
        self.exe_name = "hython.exe"
        self.name = "Houdini"

        self.init()

    def init(self):
        """Check if the scene file name has Chinese.

        Raises:
            FileNameContainsChineseError: Scene file name has Chinese.

        """
        cg_file = self.cg_file
        if utils.check_contain_chinese(cg_file):
            self.tips.add(tips_code.CONTAIN_CHINESE, cg_file)
            self.tips.save_tips()
            raise FileNameContainsChineseError

    def set_error_tips(self, error_code, error_msg):
        self.tips.add(error_code, error_msg)
        self.tips.save_tips()

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
                        # print(str(line))
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
            self.set_error_tips(tips_code.CGFILE_NOTEXISTS, cg_file)
            raise CGFileNotExistsError(ERROR_CGFILE_NOTEXIST.format(
                cg_file))
        print("_hfs_save_version---%s" % _hfs_save_version)
        return _hfs_save_version

    def _get_install_path(self, version):
        location = None
        version_str = "{0} {1}".format(self.name, version)
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
            print("User local houdini software versions===>", version_list)
        try:
            if len(version_list):
                self.allhfs = version_list
                folder_name = "Houdini {}".format(version)
                if folder_name not in version_list:
                    s_ver = folder_name.split(".", maxsplit=2)
                    b_ver = s_ver[0] + "." + s_ver[1]
                    for ver in version_list:
                        if b_ver in ver:
                            b_version = ver.split(" ")[-1]
                            print("Match large version===>", b_version)
                            return self._get_install_path(b_version)

                    error_msg = "Your houdini Software version is not any match"
                    self.logger.error("{}: {}".format(error_msg, version))
                    self.set_error_tips(tips_code.CG_NOTMATCH, error_msg)
                    raise VersionNotMatchError(VERSION_NOT_MATCH.format(version))
                else:
                    return self._get_install_path(version)
            else:
                error_msg = "Cannot found any houdini version"
                self.logger.error("{}: {}".format(error_msg, version))
                if version != "":
                    self.set_error_tips(tips_code.CG_NOTEXISTS, error_msg)
                    raise CGExeNotExistError(ERROR9899_CGEXE_NOTEXIST.format(version))
        except Exception as e:
            traceback.format_exc()
            raise e

    def find_location(self):
        """Get the path where the local Houdini startup file is located.

        Raises:
            CGExeNotExistError: The path to the startup file does not exist.

        """
        if self.linux_platform:
            exe_path = "/opt/hfs%s/bin/hython-bin" % self.version
            if not os.path.isfile(exe_path):
                num = self.version[0:2] + ".0"
                exe_path = "/opt/hfs%s/bin/hython-bin" % num
            print("exe_path---%s" % exe_path)
        else:
            location = self.location_from_reg(self.version)
            exe_path = self.exe_path_from_location(os.path.join(location, "bin"),
                                                   self.exe_name)
        if exe_path is None:
            error_msg = "Software of scene has not been found"
            self.set_error_tips(tips_code.CG_NOTEXISTS, error_msg)
            raise CGExeNotExistError(ERROR9899_CGEXE_NOTEXIST.format(
                self.name))

        self.exe_path = exe_path
        self.logger.info("exe_path: %s", exe_path)

    def analyse_cg_file(self):
        """ analyse cg file.

        Analyze the scene file to get the path to the startup file of the CG
        software.

        """
        # Find the version from the cg file
        version = self.get_save_version(self.cg_file)
        self.logger.info("version: %s", version)
        self.version = version
        self.version_str = "{0} {1}".format(self.name, version)
        self.custom_exe_path = None
        if self.custom_exe_path is not None:
            self.exe_path = self.custom_exe_path
        else:
            self.find_location()

    def valid(self):
        """Check version.

        Check whether the version of the scene file is consistent with the
        configured version.

        Raises:
            VersionNotMatchError: Version does not match.

        """
        software_config = self.task.task_info["software_config"]
        cg_version = software_config["cg_version"]
        cg_name = software_config["cg_name"]
        self.logger.debug("cg_name= %s, cg_version= %s", cg_name, cg_version)
        if (cg_name.capitalize() != self.name.capitalize()
                and cg_version != self.version):
            self.tips.add(tips_code.CG_NOTMATCH, self.version_str)
            self.tips.save_tips()
            raise VersionNotMatchError(VERSION_NOT_MATCH)

    def analyse(self):
        """Build a cmd command to perform an analysis.

        Raises:
            AnalyseFailError: Analysis scenario failed.

        """
        analyse_script_name = "houdini_analyse.py"
        analyze_script_path = os.path.join(os.path.dirname(__file__),
                                           analyse_script_name)
        task_path = self.task.task_json_path.replace("\\", "/")
        asset_path = self.task.asset_json_path.replace("\\", "/")
        tips_path = self.task.tips_json_path.replace("\\", "/")
        success_path = os.path.join(self.task.work_dir, 'analyze_sucess')

        cmd = ('"{exe_path}" "{script_full_path}" -project "{cg_file}" -task '
               '"{task_path}" -asset "{asset_path}" -tips '
               '"{tips_path}" -success "{success_path}"').format(
                   exe_path=self.exe_path,
                   script_full_path=analyze_script_path,
                   cg_file=self.cg_file,
                   task_path=task_path,
                   asset_path=asset_path,
                   tips_path=tips_path,
                   success_path=success_path)

        self.logger.debug(cmd)
        code, _, _ = self.cmd.run(cmd, shell=True)
        if code != 0:
            self.tips.add(tips_code.UNKNOW_ERR)
            self.tips.save_tips()
            raise AnalyseFailError

        # Determine whether the analysis is successful by
        #  determining whether a json file is generated.
        status, msg = self.json_exist()
        if status is False:
            self.tips.add(tips_code.UNKNOW_ERR, msg)
            self.tips.save_tips()
            raise AnalyseFailError(msg)

    def handle_analyse_result(self):
        """handle analyse result.

        Save the analyzed scene file information and texture information to
        the upload.json file.

        """
        upload_asset = []
        asset_json = self.asset_json
        normal = asset_json["Normal"]

        for _, value in normal.items():
            path_list = value[-1]
            for path in path_list:
                d = {}
                local = path
                server = utils.convert_path(local)
                d["local"] = local.replace("\\", "/")
                d["server"] = server
                upload_asset.append(d)

        # handle upload.json
        upload_asset.append({
            "local": self.cg_file.replace("\\", "/"),
            "server": utils.convert_path(self.cg_file)
        })

        upload_json = {}
        upload_json["asset"] = upload_asset

        self.upload_json = upload_json
        self.task.upload_info = upload_json

        utils.json_save(self.task.upload_json_path, upload_json)

    def run(self):
        """Perform an overall analysis process."""
        # run a custom script if exists
        # Analyze pre-custom scripts (configuration environment,
        #  specify the corresponding BAT/SH)
        # self.preAnalyseCustomScript()
        # Get scene information
        self.analyse_cg_file()
        # Basic check (whether the version of the project configuration and
        #  the version of the scenario match, etc.)
        self.valid()
        # Set task.task_info dump into a file
        self.dump_task_json()
        # Run CMD startup analysis (find the path of CG through configuration
        #  information, the path of CG can be customized)
        self.analyse()
        # Read the three json of the analysis result into memory
        self.load_output_json()
        # Write task configuration file (custom information,
        #  independent upload list), compress specific files
        # (compress files, upload path, delete path)
        self.handle_analyse_result()
        # Write cg_file and cg_id to task_info
        self.write_cg_path()

        self.logger.info("analyse end.")
