# -*- coding=utf-8 -*-
"""The plugin of the pytest.

The pytest plugin hooks do not need to be imported into any test code, it will
load automatically when running pytest.

References:
    https://docs.pytest.org/en/2.7.3/plugins.html

"""

import os
import sys

import pytest


@pytest.fixture()
def cg_file_h(tmpdir):
    """Get render config."""
    return {
        'cg_file': str(tmpdir.join('muti_layer_test.hip'))
    }


@pytest.fixture()
def houdini(tmpdir):
    """Create an houdini object fixture."""
    from rayvision_houdini.analyze_houdini import AnalyzeHoudini
    if "win" in sys.platform.lower():
        os.environ["USERPROFILE"] = str(tmpdir)
    else:
        os.environ["HOME"] = str(tmpdir)
    analyze_houdini = AnalyzeHoudini(str(tmpdir), "17.5.293")
    return analyze_houdini
