# -*- coding=utf-8 -*-
"""The plugin of the pytest.

The pytest plugin hooks do not need to be imported into any test code, it will
load automatically when running pytest.

References:
    https://docs.pytest.org/en/2.7.3/plugins.html

"""

import pytest

from rayvision_houdini.analyze_houdini import AnalyzeHoudini
from rayvision_utils.exception.exception import CGExeNotExistError


def test_get_save_version(houdini):
    """Test get_save_version function."""
    with pytest.raises(CGExeNotExistError):
        houdini.find_location()


def test_find_location(houdini, mocker, tmpdir):
    """Test find_location action."""
    mocker_cg_file = mocker.patch.object(AnalyzeHoudini, 'find_location')
    mocker_cg_file.return_value = tmpdir.join('muti_layer_test.hip')
    assert houdini.find_location() == str(tmpdir.join('muti_layer_test.hip'))
