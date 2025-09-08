#! /usr/bin/env python
#coding=utf-8
import sys
import os

script_version = "py" + "".join([str(i) for i in sys.version_info[:2]])
script_path = os.path.join(os.path.dirname(__file__))

sys.path.append(script_path)

print("python executable is: " + sys.executable)
print("python version is: " + sys.version)
print("import Analyze path: " + script_path)
sys.stdout.flush()
exec("from " + script_version + ".hanalyse import *")
