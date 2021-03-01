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
                "noise"	text NOT NULL,
                "lib"	text NOT NULL);""")
        self._conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS ions (
                "id"	integer PRIMARY KEY UNIQUE,
                "type"	text NOT NULL ,
                "number" text NOT NULL ,
                "modif" text NOT NULL ,
                "formula" text NOT NULL ,
                "sequ" text NOT NULL ,
                "radicals" integer NOT NULL ,
                "monoiso" real NOT NULL,
                "charge" integer NOT NULL,
                "int" real NOT NULL,
                "error" real NOT NULL,
                "qual" real NOT NULL,
                "noise" integer NOT NULL,
                "comment" text NOT NULL,
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