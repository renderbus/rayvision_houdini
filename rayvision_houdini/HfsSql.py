## @shen 20190329 601084713

import os,sys
import sqlite3

def connectsl(db_file='',base_table="ReFerType"):
    new_sl = False
    if not os.path.exists(db_file):
        new_sl = True
        # os.remove("D:/python folder/sql/test.db")
    sl = sqlite3.connect(db_file)
    cu = sl.cursor()

    # if new_sl:
    cu.execute('''CREATE TABLE IF NOT EXISTS %s ( TYPES   TEXT primary key  NOT NULL,INFO TEXT );'''%base_table)
    sl.commit()
    # sl.close()
    return sl,cu

def createtable_plug(connect,cur,table_name):
    cur.execute('''CREATE TABLE IF NOT EXISTS %s ( 
                HFS TEXT primary key  NOT NULL,
                HtoA TEXT,
                RedShift TEXT,unique(HFS));'''%table_name)
    connect.commit()

def updataToTable(connect,cur,table_name,parms,vales_in):
    script = ""

def getTableInfo(cur,table_name,keys,valus,parms):
    ## parms = ["TYPES"]
    script = "SELECT "
    inde = 0
    for elm in parms:
        if not inde:
            script += elm
            inde =1
        else:
            script += ", " + elm

    script += " from {table} where {keys}='{valus}'".format(table=table_name,
        keys=keys, valus=valus)
    # print(script)
    cursor = cur.execute(script)
    return cursor

def getTableInfo_typs(cur,table_name,parms):
    ## parms = ["TYPES"]
    script = "SELECT "
    inde = 0
    for elm in parms:
        if not inde:
            script += elm
            inde =1
        else:
            script += ", " + elm

    script += " from {table} ".format(table=table_name)
    # print(script)
    cursor = cur.execute(script)
    return cursor

def insertToTable(connect,cur,table_name,parms,vales_in):
    ## parms = ["TYPES"]
    ## vales_in = []
    script = "INSERT OR REPLACE INTO %s ("%table_name
    vales = " VALUES ("
    inde = 0
    for elm in parms:
        if not inde:
            script += elm
            vales += "?"
            inde =1
        else:
            script += ", " + elm
            vales += ",?"

    script += " )" + vales + ")"
    # print(script)
    cur.execute(script,vales_in)
    connect.commit()


def main():
    type_list = ["file","tex","map"]
    sl,cu = connectsl()
    table_name = "ReFerType"
    cursor = getTableInfo(cu,table_name,["TYPES"])
    ## get typelist
    typelist = []
    for elm in cursor:
        print("elm",elm)
        typelist.append(elm[0])

    print(typelist)
    for elm in type_list:
        if not elm in typelist:
            insertToTable(sl,cu,table_name,["TYPES"],[elm])


if __name__ == '__main__':
    main()
