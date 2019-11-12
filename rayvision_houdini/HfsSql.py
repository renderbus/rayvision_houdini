"""Connect to the sqlite interface."""

import sqlite3


def connectsl(db_file='', base_table="ReFerType"):
    """Connect to sqlite

    :param str db_file: sqlite databse name, default is empty string.
    :param base_table: sqlite table name, default 'ReFerType'.
    :return tuple: connect object, cursor object.
    """
    sl = sqlite3.connect(db_file)
    cu = sl.cursor()

    cu.execute(
        '''CREATE TABLE IF NOT EXISTS %s ( TYPES   TEXT primary key  NOT NULL,
        INFO TEXT );''' % base_table)
    sl.commit()
    return sl, cu


def createtable_plug(connect, cur, table_name):
    """Create table plugin.

    :param connect: connect object.
    :param cur: cursor object.
    :param str table_name: sqlite table name.
    """
    cur.execute('''CREATE TABLE IF NOT EXISTS %s (
                HFS TEXT primary key  NOT NULL,
                HtoA TEXT,
                RedShift TEXT,unique(HFS));''' % table_name)
    connect.commit()


def getTableInfo(cur, table_name, keys, valus, parms):
    """Get table information.

    :param object cur: sqlite cursor object
    :param str table_name:
    :param str keys: key word is user to filter result from table.
    :param str valus: value is user to filter result from table.
    :param list parms: type, example ["file", "tex", "map"].
    :return: sqlite3.Cursor object.
    """
    script = "SELECT "
    inde = 0
    for elm in parms:
        if not inde:
            script += elm
            inde = 1
        else:
            script += ", " + elm

    script += " from {table} where {keys}='{valus}'".format(table=table_name,
                                                            keys=keys,
                                                            valus=valus)
    cursor = cur.execute(script)
    return cursor


def getTableInfo_typs(cur, table_name, parms):
    """Get table information according to type.

    :param object cur: sqlite cursor object.
    :param string table_name: sqlite table name.
    :param list parms: type, example ["file", "tex", "map"].
    :return: sqlite3.Cursor object.
    """
    script = "SELECT "
    inde = 0
    for elm in parms:
        if not inde:
            script += elm
            inde = 1
        else:
            script += ", " + elm

    script += " from {table} ".format(table=table_name)
    # print(script)
    cursor = cur.execute(script)
    return cursor


def insertToTable(connect, cur, table_name, parms, vales_in):
    """Insert information to table.

    :param object connect: sqlite connect object.
    :param object cur: sqlite cursor object.
    :param string table_name: sqlite table name.
    :param parms: type, example ["file", "tex", "map"].
    :param vales_in: type, example ["file", "tex", "map"].
    """
    script = "INSERT OR REPLACE INTO %s (" % table_name
    vales = " VALUES ("
    inde = 0
    for elm in parms:
        if not inde:
            script += elm
            vales += "?"
            inde = 1
        else:
            script += ", " + elm
            vales += ",?"

    script += " )" + vales + ")"
    # print(script)
    cur.execute(script, vales_in)
    connect.commit()


def main():
    """Methon for sqlite.

    Connect to the sqlite database and filter the data for more types,
    then insert the data that meets the requirements into the database.
    """
    type_list = ["file", "tex", "map"]
    sl, cu = connectsl()
    table_name = "ReFerType"
    cursor = getTableInfo_typs(cu, table_name, ["TYPES"])
    typelist = []
    for elm in cursor:
        typelist.append(elm[0])

    for elm in type_list:
        if elm not in typelist:
            insertToTable(sl, cu, table_name, ["TYPES"], [elm])


if __name__ == '__main__':
    main()
