#!/usr/bin/env python
"""A houdini analyze interface."""

import os
import sys
import json
import argparse
import re
import hou  # pylint: disable=import-error

import HfsSql


class HoudiniAnalyse:
    """A core class for Houdini analysis."""
    runcode = True
    runend = False

    def __init__(self, args):
        self._args = args
        self._ext = [".py", ".hda"]
        self.sequence_type_list = [r"%(UDIM)d", r"<udim>"]
        self.task_adict = {}
        self._temp_path = None
        self._refer_table = "ReFerType"
        self._sl = None
        self._cur = None
        self._typelist = list()
        self.hip_file = self._args.project.replace("\\", "/")
        self.tips_adict = dict()
        self.asset_adict = dict()
        self.create_base_date()

    def create_base_date(self):
        """Create sqlite data."""
        if os.path.exists(self._args.task):
            with open(self._args.task, "rb") as f:
                self.task_adict = json.load(f)
                f.close()

        _temp_path = os.path.dirname(sys.argv[0])
        self._temp_path = "%s/data_tl.db" % _temp_path.replace("\\", "/")
        new_data = True if not os.path.exists(self._temp_path) else False

        self._sl, self._cur = HfsSql.connectsl(self._temp_path,
                                               self._refer_table)
        if new_data:
            HfsSql.insertToTable(self._sl, self._cur, self._refer_table,
                                 ["TYPES"], ["file"])

        self.get_node_type_data()

    def get_node_type_data(self):
        """Gets a list of node types"""
        cursor = HfsSql.getTableInfo_typs(self._cur, self._refer_table,
                                          ["TYPES"])
        for elm in cursor:
            self._typelist.append(elm[0])
        print_times(self._typelist)

    def load_hip_file(self):
        """load hip file."""
        try:
            hou.setSimulationEnabled(False)
            hou.setUpdateMode(hou.updateMode.Manual)
            print("set Simulation off")
            print("set updateMode Manual")
        except OSError as e:
            print(e)

        if os.path.exists(self.hip_file):
            print_times("Loading hip file: %s" % self.hip_file)
            try:
                hou.hipFile.load(self.hip_file)
                print_times("Loading hip file success")
                _hip_val = os.path.dirname(self.hip_file)
                hou.hscript("setenv HIP=" + str(_hip_val))
                hou.hscript("varchange")
            except (IOError, ZeroDivisionError) as e:
                print_times(e)
        else:
            print_times("ERROR: the hip file is not exist!")
            sys.exit(1)

    def get_assets(self):
        """Get asset information."""
        if not self.runcode:
            self.runend = True
            sys.exit(886)
        miss_adict = {}
        normal_adict = {}
        folder_adict = {}
        search_adict = {}
        file_adict = hou.fileReferences()
        for elm in file_adict:
            if elm[0] is not None and elm[0].name() not in ['prerender',
                                                            "preframe",
                                                            "postframe",
                                                            "postwrite",
                                                            "postrender"]:
                print_times("Strart--: {0}".format(elm[0]))
                print_times("elm[0].eval(): {0}".format(elm[0].eval()))
                if self.is_file(self.str_to_unicode(str(elm[0].eval()))):
                    print_times("File in : {0}".format(elm[0].eval()))
                    if not elm[0].name() in self._typelist and len(elm[-1]):
                        if not os.path.splitext(elm[-1])[-1] in self._ext:
                            HfsSql.insertToTable(self._sl, self._cur,
                                                 self._refer_table,
                                                 ["TYPES"], [elm[0].name()])
                            self._typelist.append(elm[0].name())
                        else:
                            pass

                    if self.is_file(self.str_to_unicode(elm[-1])):
                        print_times(
                            "File in str_to_unicode: {0}".format(elm[-1]))
                        file_split = os.path.split(elm[0].eval())
                        print_times(file_split)
                        if elm[0].eval() not in search_adict:
                            if not file_split[0] in folder_adict:
                                print_times("From folder...")
                                is_sq, return_file, dif_files = (
                                    self.is_sequence(file_split[0],
                                                     self.type_fit(
                                                         file_split[1])))
                                folder_adict[file_split[0]] = dif_files
                                print_times(return_file)
                            else:
                                print_times("From list...")
                                is_sq, return_file, dif_files = (
                                    self.is_sequence(file_split[0],
                                                     self.type_fit(
                                                         file_split[1]),
                                                     folder_adict[
                                                         file_split[0]]))
                                folder_adict[file_split[0]] = dif_files
                                print_times(return_file)
                            normal_adict, miss_adict = self.asset_edit(
                                elm, is_sq, return_file, file_split[0],
                                normal_adict, miss_adict)
                            search_adict[elm[0].eval()] = [is_sq,
                                                           return_file]
                        else:
                            # Find it in search_adict
                            returns = search_adict[elm[0].eval()]
                            normal_adict, miss_adict = self.asset_edit(
                                elm, returns[0], returns[1],
                                file_split[0], normal_adict, miss_adict)

                    elif not elm[-1]:
                        # Check types
                        print(elm)
                        if elm[0].name() in self._typelist:
                            pass
                    else:
                        print("-" * 80)
                        print("DO FILT")
                        print_times(elm)
            print_times("Ebd: {0}".format(elm[0]))

        print("self.runcode-----%s" % self.runcode)
        self.asset_adict = {"Normal": normal_adict, "Miss": miss_adict,
                            "camera": self.check_camera()}

        self.tips_info()
        self.write_file(self.asset_adict, self._args.asset, 'json')
        self.write_file(self.tips_adict, self._args.tips, 'json')

    def type_fit(self, filename):
        """cleaning filename."""
        if not self.runcode:
            self.runend = True
            sys.exit(886)
        for stype in self.sequence_type_list:
            if stype in filename:
                filename = filename.replace(stype, "1001")
        return filename

    def tips_info(self):
        """Get tips info."""
        if not self.runcode:
            self.runend = True
            sys.exit(886)

        info_temp = ""
        print("=" * 25 + " Tips Info " + "=" * 25)
        if "Miss" in self.asset_adict:
            keyword_war = '50001'  # Just for warnning
            infos_list = []
            if len(self.asset_adict["Miss"]):
                for nodes in self.asset_adict["Miss"]:
                    asset_type_adict = self.asset_adict["Miss"][nodes]
                    print("Nodes: %s" % nodes)
                    print("File name: %s" % asset_type_adict[0])
                    if len(asset_type_adict[-1]) == 1:
                        print("Miss file: %s" % asset_type_adict[-1][0])
                        info_temp = ("Nodes: %s  File name: %s  miss file: %s"
                                     " " % (nodes, asset_type_adict[0],
                                            asset_type_adict[-1][0]))
                    elif len(asset_type_adict[-1]) > 1:
                        print("Miss files: %s" % str(asset_type_adict[-1]))
                        info_temp = ("Nodes: %s  File name: %s  miss file: %s"
                                     " " % (nodes, asset_type_adict[0],
                                            str(asset_type_adict[-1])))
                    infos_list.append(info_temp)
                    print("-" * 80)
            if len(infos_list):
                self.tips_adict[keyword_war] = infos_list

        if "camera" in self.asset_adict:
            print("-" * 23 + " Cameras Info " + "-" * 23)
            keyword_err = '50002'
            keyword_war = '50003'
            infos_list_err = []
            infos_list_war = []
            if "diff" in self.asset_adict["camera"]:
                print(">> With diffrence values")
                for elm in self.asset_adict["camera"]["diff"]:
                    print(elm)
                    if len(elm) > 1:
                        base_input = elm.keys()[0]
                        for key in elm.keys():
                            if len(key) < len(base_input):
                                base_input = key
                        print("Base Nodes: %s  file: %s " % (
                            base_input, elm[base_input][0]))
                        info_temp = (
                            "Nodes with diffrence file val: %s " %
                            base_input)
                        for nd in elm:
                            if nd != base_input:
                                if elm[nd][1] == 0:
                                    print(
                                        "Nodes with diffrence file val: %s"
                                        " " % nd)
                                    print("File: %s " % elm[nd][0])
                    else:
                        print("Errors...(camera checks) ")
                    infos_list_war.append(info_temp)
                    print("-" * 80)
                print("-" * 80)
                if len(infos_list_war):
                    self.tips_adict[keyword_war] = infos_list_war

            if "miss" in self.asset_adict["camera"]:
                for elm in self.asset_adict["camera"]["miss"]:
                    if len(elm) > 1 and "node_name" not in elm:
                        print(">> Camera did not exist.")
                        print("Nodes: %s  \nMiss: %s" % (
                            elm.keys()[0], elm[elm.keys()[0]][0]))
                        info_temp = ("Nodes: %s  Miss: %s" % (
                            elm.keys()[0], elm[elm.keys()[0]][0]))
                    else:
                        print(
                            ">> Camera did not exist(the cam path which in the"
                            " rop node is not exist).")
                        print(
                            "Nodes: %s  \nMiss: This camera is not in"
                            " the .hip file." %
                            elm.keys()[0])
                        info_temp = ("Node: %s Missing camera: %s." % (
                            elm['node_name'], elm.keys()[0]))
                    infos_list_err.append(info_temp)
                    print("-" * 80)

            if "normal" in self.asset_adict["camera"]:
                if len(self.asset_adict["camera"]["normal"]):
                    if len(infos_list_err):
                        if len(infos_list_war):
                            self.tips_adict[keyword_war].extend(infos_list_err)
                        else:
                            self.tips_adict[keyword_war] = infos_list_err
                else:
                    if len(infos_list_err):
                        self.tips_adict[keyword_err] = infos_list_err
            else:
                if len(infos_list_war):
                    self.tips_adict[keyword_err] = infos_list_war
                    if len(infos_list_err):
                        self.tips_adict[keyword_err].extend(infos_list_err)
                elif len(infos_list_err):
                    self.tips_adict[keyword_err] = infos_list_err

    def analy_info(self):
        """analyse houdini CG information """
        if not self.runcode:
            self.runend = True
            sys.exit(886)
        print_times("Analysis start...")
        rop_node, geo_node, geo_nodes, rop_nodes = (list(), list(), dict(),
                                                    dict())
        geo_info, geo_flag_count = "", 0
        rop_info, rop_flag_count = "", 0
        print_times("Searching Geometrry Rops...")

        for obj in hou.node('/').allSubChildren():
            obj_path = obj.path().replace('\\', '/')
            obj_type_name = obj.type().name()
            render_node = hou.node(obj_path)
            if obj_type_name in ['geometry', 'rop_geometry']:
                if render_node.parm("execute"):
                    print_times("Geometry ROP: %s" % render_node)
                    if geo_flag_count > 0:
                        geo_info += '\n'
                    geo_info += obj_path
                    geo_nodes["node"] = obj_path
                    geo_info += '|' + str(obj.evalParm('f1'))
                    geo_info += '|' + str(obj.evalParm('f2'))
                    geo_info += '|' + str(obj.evalParm('f3'))
                    pass_frame = str(int(obj.evalParm('f3'))) if int(
                        obj.evalParm('f3')) > 0 else "1"
                    geo_nodes["frames"] = "%s-%s[%s]" % (
                        str(int(obj.evalParm('f1'))),
                        str(int(obj.evalParm('f2'))), pass_frame)
                    geo_info += '|' + '0'
                    geo_nodes["option"] = '0'
                    geo_nodes["render"] = "0"
                    geo_node.append(geo_nodes.copy())
                    geo_flag_count += 1
            elif obj_type_name in ['ifd', 'arnold', 'Redshift_ROP']:
                print_times("Render ROP: %s" % render_node)
                if rop_flag_count > 0:
                    rop_info += '\n'
                rop_info += obj_path
                rop_info += '|' + str(obj.evalParm('f1'))
                rop_info += '|' + str(obj.evalParm('f2'))
                rop_info += '|' + str(obj.evalParm('f3'))
                rop_info += '|' + '-1'

                rop_nodes["node"] = obj_path
                pass_frame = str(int(obj.evalParm('f3'))) if int(
                    obj.evalParm('f3')) > 0 else "1"
                rop_nodes["frames"] = "%s-%s[%s]" % (
                    str(int(obj.evalParm('f1'))), str(int(obj.evalParm('f2'))),
                    pass_frame)
                rop_nodes["option"] = '-1'
                rop_nodes["render"] = "0" if obj.isBypassed() else "1"
                rop_node.append(rop_nodes.copy())
                rop_flag_count += 1
        print_times("Total Render Nodes: %s" % geo_flag_count)
        print_times("Total Render ROPs: %s" % rop_flag_count)
        print("geo_node----%s" % geo_node)
        print("rop_node----%s" % rop_node)

        scene_info = {"geo_node": geo_node, "rop_node": rop_node}
        self.task_adict["scene_info"] = scene_info
        print("scene_info----%s" % self.task_adict["scene_info"])
        print("self._args.task----%s" % self._args.task)
        self.write_file(self.task_adict, self._args.task, 'json')

        print_times("Analysis end...")

    def check_camera(self):
        """Check camera.

        :return: dict
        """
        if not self.runcode:
            self.runend = True
            sys.exit(886)
        print_times("CheckCamera start...")
        ropnodes = self.task_adict["scene_info"]["rop_node"]
        camera_adict = {}
        if len(ropnodes):
            cam_normal = []
            cam_diff = []
            cam_miss = []

            for elm in ropnodes:
                n = hou.node(elm["node"])
                cam = None
                for i in n.parms():
                    if i.name() == "camera":
                        cam = n.parm("camera").eval()
                    elif i.name() == "RS_renderCamera":
                        cam = n.parm("RS_renderCamera").eval()

                if hou.node(cam):
                    print_times("abc_find start...")
                    returns = self.abc_find(cam)
                    if returns[0] == 'normal':
                        print("Normal abc cameras")
                        cam_normal.append(returns[1])
                    elif returns[0] == 'diff':
                        print("Diffrence abc cameras")
                        cam_diff.append(returns[1])
                    elif returns[0] == 'miss':
                        print("Miss abc cameras")
                        cam_miss.append(returns[1])
                    else:
                        print("This camera is in the .hip file.")
                        cam_normal.append({cam: "exist"})
                else:
                    print("This camera is not in the .hip file.")
                    cam_miss.append({cam: "notexist", "node_name":elm['node']})
            if len(cam_normal):
                camera_adict["normal"] = cam_normal
            if len(cam_diff):
                camera_adict["diff"] = cam_diff
            if len(cam_miss):
                camera_adict["miss"] = cam_miss
        print("camera_adict---%s" % camera_adict)
        return camera_adict

    @staticmethod
    def abc_find(path):
        """ find for abc"""
        if not HoudiniAnalyse.runcode:
            HoudiniAnalyse.runend = True
            sys.exit(886)
        print("abc_find is working")
        return_key = 'notfit'
        temp_adict = {}
        print("path----%s" % path)
        if path != "":
            cam_pl = path.split("/")
            print("len(cam_pl)----%s" % len(cam_pl))
            if len(cam_pl) > 0:
                node_pre = ""
                n_types = ["alembicarchive", "alembicxform", "cam"]
                pathval = {}
                index = 1
                type_abc = False
                first_key = ""
                for elm in cam_pl:
                    if not elm:
                        node_pre += "/" + elm
                        if hou.node(node_pre).type().name() in n_types:
                            if index == 1:
                                if (hou.node(node_pre).type().name()
                                        == "alembicarchive"):
                                    type_abc = True
                                    first_key = node_pre
                            if type_abc:
                                p_val = hou.node(node_pre).parm(
                                    "fileName").eval()
                                pathval[node_pre] = p_val
                            index += 1
                print("len(pathval)----%s" % len(pathval))
                if len(pathval) > 2:
                    vals = pathval[first_key]
                    abc_base = False if not os.path.exists(vals) else True
                    same_p = True
                    temp_adict = {}
                    return_key = 'normal'
                    for elm in pathval:
                        diff_path = []
                        if not pathval[elm] == vals:
                            if not os.path.exists(pathval[elm]):
                                same_p = False
                                diff_path.append(pathval[elm])
                                # Whether if the same file with the first
                                # file in
                                diff_path.append(
                                    0)
                                diff_path.append("notexist")
                            else:
                                same_p = False
                                diff_path.append(pathval[elm])
                                diff_path.append(0)
                                diff_path.append("exist")
                            temp_adict[elm] = diff_path

                        else:
                            if not os.path.exists(pathval[elm]):
                                diff_path.append(pathval[elm])
                                diff_path.append(1)
                                diff_path.append("notexist")
                            else:
                                diff_path.append(pathval[elm])
                                diff_path.append(1)
                                diff_path.append("exist")
                            temp_adict[elm] = diff_path
                    if abc_base:
                        if same_p:
                            return_key = 'normal'
                        else:
                            return_key = 'diff'
                    else:
                        return_key = 'miss'

        return return_key, temp_adict

    @staticmethod
    def asset_edit(node_turp, is_sq, fileadict, file_path, normal_adict,
                   miss_adict):
        """Edit asset information."""
        if not HoudiniAnalyse.runcode:
            HoudiniAnalyse.runend = True
            sys.exit(886)
        if is_sq == 0:
            # print("0 is sequence")
            # {"abc":[["abc.0001.exr","abc.0002.exr"..."abc.0010.exr"],
            # 1,10,4,abc.$F4.exr]}
            file_temp = []
            for elm in fileadict[fileadict.keys()[0]][0]:
                file_temp.append("%s/%s" % (file_path.replace("\\", "/"), elm))
            # print(file_temp)
            node_path = node_turp[0].node().path()
            if node_path not in normal_adict:
                normal_adict[node_path] = [node_turp[-1], file_temp]
            else:
                normal_adict[node_path][-1].extend(file_temp)

        elif is_sq == 1:
            # print("1 not sequence")
            fs_list = ["$F", "$F2", "$F3", "$F4", "$F5"]
            node_path = node_turp[0].node().path()
            file_temp = "%s/%s" % (file_path.replace("\\", "/"), fileadict)
            # if its a list type
            for elm in fs_list:
                if elm in node_turp[-1]:
                    if node_path not in miss_adict:
                        miss_adict[node_path] = [node_turp[-1], [file_temp]]
                    else:
                        miss_adict[node_path][-1].extend([file_temp])
            if node_path not in normal_adict:
                normal_adict[node_path] = [node_turp[-1], [file_temp]]
            else:
                normal_adict[node_path][-1].extend([file_temp])
        elif is_sq == 2:
            # print("2 file not exist")
            node_path = node_turp[0].node().path()
            file_temp = "%s/%s" % (file_path.replace("\\", "/"), fileadict)
            if node_path not in miss_adict:
                miss_adict[node_path] = [node_turp[-1], [file_temp]]
            else:
                # print(miss_adict[node_path])
                miss_adict[node_path][-1].extend([file_temp])

        elif is_sq == 3:
            print_times("error input")

        return normal_adict, miss_adict

    @staticmethod
    def is_file(pathvale):
        """Determine if the file exists.

        :param string pathvale: path.
        :return: bool.
        """
        if not HoudiniAnalyse.runcode:
            HoudiniAnalyse.runend = True
            sys.exit(886)
        is_file_path = False
        persent = 0
        drive_spl = os.path.splitdrive(pathvale)
        ext_spl = os.path.splitext(pathvale)
        along_spl = os.path.split(pathvale)
        if pathvale.replace("\\", "/").startswith("//"):
            persent += 7
        if len(drive_spl[0]) and len(drive_spl[-1]):
            persent += 7
        if "/" in along_spl[0].replace("\\", "/"):
            persent += 4
            ss = re.findall("[/*,//]", ext_spl[0].replace("\\", "/"))
            if len(ss) > 1:
                persent += 1
        if len(ext_spl[-1]):
            persent += 5
        if "$HIP/" in pathvale.replace("\\", "/"):
            persent += 7
        if persent > 9:
            is_file_path = True

        return is_file_path

    @staticmethod
    def get_encode(encode_str):
        """Access encoding mode.

        :param string encode_str: string to be detected.
        :return: string.
        """
        _dcode_list = [sys.getfilesystemencoding(), "utf-8", "gb18030", "ascii",
                       "gbk", "gb2312"]
        if isinstance(encode_str, unicode):  # pylint: disable=undefined-variable
            return "unicode"
        else:
            for code in _dcode_list:
                try:
                    encode_str.decode(code)
                    return code
                except Exception:
                    pass

    @classmethod
    def str_to_unicode(cls, encode_str):
        """Convert the string to unicode.

        :param string encode_str: string to be detected.
        :return: string.
        """
        if not encode_str:
            encode_str = ""
            return encode_str
        elif isinstance(encode_str, unicode):  # pylint: disable=undefined-variable
            return encode_str
        else:
            code = cls.get_encode(encode_str)
            return encode_str.decode(code)

    @classmethod
    def is_sequence(cls, dirt='', filename='', adict_in=()):
        """Filter by sequence."""
        if not cls.runcode:
            cls.runend = True
            sys.exit(886)
        # is_sequence: 0 is sequence; 1 not sequence; 2 file not exist; 3 error
        is_sequence = 1
        print_times("Start ssq.{0}&&{1}".format(dirt, filename), "debug")
        if filename != "":
            sequence_adict = {}
            maby_sequence = True
            dif_list = []
            maby_sequence, split_str, num = cls.getnumber(filename)
            print_times("{0} {1} {2}".format(maby_sequence, split_str, num),
                        "debug")
            All_files = os.listdir(dirt) if not len(
                adict_in) and os.path.exists(dirt) else adict_in
            if maby_sequence:
                sequence_list = []
                for elm in All_files:
                    _maby_sequence, _split_str, _num = cls.getnumber(elm)
                    if _maby_sequence:
                        elm_split = elm.split(_split_str)
                        filename_list = filename.split(split_str)
                        if filename_list[0] == elm_split[0] and (
                                elm_split[-1] == filename_list[-1]):
                            if elm not in sequence_list:
                                sequence_list.append(elm)
                        else:
                            dif_list.append(elm)
                    else:
                        dif_list.append(elm)
                if len(sequence_list) > 2:
                    is_sequence = 0
                    i = 0
                    seq_name = ''
                    # seq_len = 0
                    min_num = 0
                    max_num = 0
                    first_elm = ''
                    for elm in sequence_list:
                        num = cls.getnumber(elm)[2]
                        if i == 0:
                            min_num = int(num)
                            first_elm = elm
                        # if i == len(sequence_list) - 1:
                        #     seq_len_end = len(num)
                        if int(num) < min_num:
                            min_num = int(num)
                            first_elm = elm
                        if int(num) > max_num:
                            max_num = int(num)
                        i += 1
                    # print("%s sequence from %d to %d"%(seq_name,min_num,
                    # max_num))
                    # maybes, split_str_1, num_1 = cls.getnumber(first_elm)
                    _, split_str_1, num_1 = cls.getnumber(first_elm)
                    seq_name = first_elm.split(split_str_1)[0]
                    end_with = first_elm.split(split_str_1)[-1]
                    if len(num_1) > 1:
                        file_replace_name = seq_name + split_str_1.replace(
                            num_1, "$F%d" % len(num_1)) + end_with
                    else:
                        file_replace_name = seq_name + split_str_1.replace(
                            num_1, "$F") + end_with

                    sequence_adict[seq_name] = [sequence_list, min_num, max_num,
                                                len(num_1), file_replace_name]
                    return is_sequence, sequence_adict, dif_list
                else:
                    maby_sequence = False
            if not maby_sequence:
                file_path = os.path.abspath(os.path.join(dirt, filename))
                if os.path.exists(file_path):
                    # exist ,but not a sequence
                    if len(adict_in):
                        if filename in adict_in:
                            adict_in.remove(filename)
                        dif_list.extend(adict_in)
                    else:
                        if filename in All_files:
                            All_files.remove(filename)
                        dif_list.extend(All_files)
                    return is_sequence, filename, dif_list
                else:
                    # print("this file is not exist.")
                    if len(adict_in):
                        dif_list.extend(adict_in)
                    else:
                        dif_list.extend(All_files)
                    return 2, filename, dif_list
        else:
            print_times("Please set the filename for this function.")
            return 3, "Please set the filename for this function.", []

    @staticmethod
    def getnumber(filename):
        """Get number."""
        if not HoudiniAnalyse.runcode:
            HoudiniAnalyse.runend = True
            sys.exit(886)
        maby_sequence = True
        split_str = ''
        num = ''
        with_num = re.findall(r"\d+", filename)
        if len(with_num) > 0:
            num = with_num[-1]
            # num_len = len(with_num[-1])
            if "." + with_num[-1] + "." in filename:
                split_str = "." + with_num[-1] + "."
            elif with_num[-1] + "." in filename:
                split_str = with_num[-1] + "."
            else:
                maby_sequence = False
                # print("Not sequence")
        else:
            maby_sequence = False
            # print("Without Numbers")
        return maby_sequence, split_str, num

    @staticmethod
    def write_file(info, file, types='txt'):
        """Write information to file.

        :param info: A info need to write in file.
        :param file: file path.
        :param types: file suffix.
        """
        if not HoudiniAnalyse.runcode:
            HoudiniAnalyse.runend = True
            sys.exit(886)
        if types == 'txt':
            with open(file, "w") as f:
                f.write(str(info))
                f.close()
        elif types == 'json':
            with open(file, "w")as f:
                json.dump(info, f, indent=2)
                f.close()


def set_runcode():
    """Set run code in platform,
    only support window and linux.
    """
    f = "C:/temp/deg.mc"
    f_linux = "/tmp/deg.mc"
    if os.path.exists(f) or os.path.exists(f_linux):
        HoudiniAnalyse.runcode = False


def set_args():
    """Receive command line arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-project', type=str, required=True,
                        help='.hip file to load')
    parser.add_argument('-task', type=str, required=True,
                        help='the task file .json path')
    parser.add_argument('-asset', type=str, required=True,
                        help='the asset file .json path')
    parser.add_argument('-tips', type=str, required=True,
                        help='the tips file .json path')
    parser.add_argument('-success', type=str, required=False,
                        help='whether analyse success')
    args = parser.parse_args()
    # print(args)
    return args


def analyse_main(args):
    """The main program for Houdini analyzes."""
    houdini_analyse_obj = HoudiniAnalyse(args)
    print_times('Load hip file start...')
    try:
        houdini_analyse_obj.load_hip_file()
    except Exception:
        print_times('Load hip ignore Errors.')
    print_times('Load hip file end.')
    set_runcode()
    houdini_analyse_obj.analy_info()
    houdini_analyse_obj.get_assets()
    print(HoudiniAnalyse.runcode, HoudiniAnalyse.runend)


def print_times(info, ext="info"):
    """Print times."""
    if ext == "info":
        print(str(info))
    else:
        print("[debug]{0}".format(str(info)))


if __name__ == "__main__":
    print("\n")
    print("*" * 80)
    print("Python version: %s" % sys.version)
    print("\n")
    command_line_params = set_args()
    analyse_main(command_line_params)
