import sqlite3
from os.path import join

from src import path


class SearchRepository(object):
    def __init__(self):
        self._conn = sqlite3.connect(join(path,"src","data",'search.db'))

    def makeTables(self):
        self._conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS searches (
                "id"	integer PRIMARY KEY UNIQUE ,
                "name"	text NOT NULL UNIQUE ,
                "sequName"	text NOT NULL ,
                "charge"	text NOT NULL ,
                "fragmentation"	text NOT NULL,
                "nrMod"	text NOT NULL ,
                "spectralData"	text NOT NULL,
                "noise"	text NOT NULL);""")
        self._conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS ions (
                "id"	integer PRIMARY KEY UNIQUE,
                "name"	text NOT NULL ,
                "gain" text NOT NULL ,
                "loss" text NOT NULL ,
                "residue" text NOT NULL ,
                "radicals" integer NOT NULL ,
                "direct" integer NOT NULL ,
                "enabled" integer NOT NULL,
                "deleted" integer NOT NULL,
                "searchId" integer NOT NULL );""")
        self._conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS peaks (
                "id"	integer PRIMARY KEY UNIQUE,
                "name"	text NOT NULL ,
                "gain" text NOT NULL ,
                "loss" text NOT NULL ,
                "residue" text NOT NULL ,
                "radicals" integer NOT NULL ,
                "enabled" integer NOT NULL,
                "ionId" integer NOT NULL );""")