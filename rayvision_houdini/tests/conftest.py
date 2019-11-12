"""The plugin of the pytest.

The pytest plugin hooks do not need to be imported into any test code, it will
load automatically when running pytest.

References:
    https://docs.pytest.org/en/2.7.3/plugins.html

"""
import pytest

from rayvision_api.task.handle import RayvisionTask

from rayvision_houdini.HfsSql import connectsl


@pytest.fixture()
def connect():
    """Connect fixture."""
    return connectsl()[0]


@pytest.fixture()
def cursor():
    """cursor fixture."""
    return connectsl()[1]


@pytest.fixture()
def refer_table():
    """cursor fixture."""
    return "ReFerType"


@pytest.fixture()
def user_info():
    """user info fixture."""
    return {
        "domain": "task.renderbus.com",
        "platform": "2",
        "access_id": "df6d1d6s3dc56ds6",
        "access_key": "fa5sd565as2fd65",
        "local_os": 'windows',
        "workspace": "c:/workspace",
        "render_software": "Houdini",
        "software_version": "17.5.293",
        "project_name": "Project1",
        "plugin_config": {}
    }


@pytest.fixture()
def cg_file_h(tmpdir):
    """Get render config."""
    return {
        'cg_file': str(tmpdir.join('muti_layer_test.hip'))
    }


@pytest.fixture()
def task(user_info, cg_file_h, mocker):
    """Create an RayvisionTask fixture."""
    mocker_task_id = mocker.patch.object(RayvisionTask, 'get_task_id')
    mocker_task_id.return_value = '1234567'
    mocker_user_id = mocker.patch.object(RayvisionTask, 'get_user_id')
    mocker_user_id.return_value = '10000012'
    mocker_user_id = mocker.patch.object(RayvisionTask,
                                         'check_and_add_project_name')
    mocker_user_id.return_value = '147258'
    return RayvisionTask(cg_file=cg_file_h['cg_file'], **user_info)


@pytest.fixture()
def houdini(cg_file_h, task):
    """Create an houdini object fixture."""
    from rayvision_houdini.cg import Houdini
    return Houdini(str(cg_file_h['cg_file']), task, 2004, '')
