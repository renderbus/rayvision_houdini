"""Test HfsSql."""

from rayvision_houdini.HfsSql import getTableInfo_typs
from rayvision_houdini.HfsSql import insertToTable


def test_insertToTable(connect, cursor, refer_table):
    """Test inesrt to table function"""
    result = insertToTable(connect, cursor, refer_table, ["TYPES"], ["file"])
    assert isinstance(result, object)


def test_getTableInfo_typs(cursor, refer_table):
    """Test get table info function according types"""
    result = getTableInfo_typs(cursor, refer_table, ["TYPES"])
    assert isinstance(result, object)
