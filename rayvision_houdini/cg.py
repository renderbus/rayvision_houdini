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
from rayvision_utils.exception.exception import VersionNotMatchError
from rayvision_utils.exception.exception import AnalyseFailError
from rayvision_utils.exception.error_msg import VERSION_NOT_MATCH
from rayvision_utils.exception.error_msg import ERROR9899_CGEXE_NOTEXIST


VERSION = sys.version_info[0]


class Houdini(JsonHandle):
    """
    Houdini
    """

    def __init__(self, *args, **kwargs):
        super(Houdini, self).__init__(*args, **kwargs)
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

    @staticmethod
    def get_save_version(cg_file):
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
            print("The .hip file is not exist.")
            _hfs_save_version, _hip_save_val = ("", "")
        print("_hfs_save_version---%s" % _hfs_save_version)
        return _hfs_save_version

    def location_from_reg(self, version):
        """Get the path in the registry of the local CG.

        When the system environment is Windows, get the path where the local
        Maya startup file is located in the registry.

        Args:
            version (str): Houdini version.
                e.g.:
                    "17.0.352".

        Returns:
            str: The path where Houdini's startup files are located.
                e.g.:
                    "C:/Program Files/Side Effects Software/Houdini 17.0.352/
                    bin/houdini.exe".

        """
        try:
            import _winreg
        except ImportError:
            import winreg as _winreg

        version_str = "{0} {1}".format(self.name, version)

        location = None

        string = 'SOFTWARE\\Side Effects Software\\{0}'.format(version_str)
        print("string---%s" % string)
        self.logger.info(string)
        try:
            handle = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, string)
            location, type1 = _winreg.QueryValueEx(handle, "InstallPath")
            self.logger.debug("%s %s", location, type1)
        except Exception:
            msg = traceback.format_exc()
            self.logger.error(msg)
            raise Exception(
                "Could not find the %s of software on your machine " %
                version_str)
        return location

    def find_location(self):
        """Get the path where the local Houdini startup file is located.

        Raises:
            CGExeNotExistError: The path to the startup file does not exist.

        """
        location = self.location_from_reg(self.version)
        exe_path = self.exe_path_from_location(os.path.join(location, "bin"),
                                               self.exe_name)
        if exe_path is None:
            self.tips.add(tips_code.CG_NOTEXISTS, self.version_str)
            self.tips.save_tips()
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
        analyse_script_name = "Analyze.py"
        analyze_script_path = os.path.join(os.path.dirname(__file__),
                                           analyse_script_name)
        task_path = self.task.task_json_path.replace("\\", "/")
        asset_path = self.task.asset_json_path.replace("\\", "/")
        tips_path = self.task.tips_json_path.replace("\\", "/")

        cmd = ('"{exe_path}" "{script_full_path}" -project "{cg_file}" -task '
               '"{task_path}" -asset "{asset_path}" -tips '
               '"{tips_path}"').format(
                   exe_path=self.exe_path,
                   script_full_path=analyze_script_path,
                   cg_file=self.cg_file,
                   task_path=task_path,
                   asset_path=asset_path,
                   tips_path=tips_path)

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
