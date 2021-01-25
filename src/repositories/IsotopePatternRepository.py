import csv
import os
import sqlite3
from os.path import join

import numpy as np

from src import path
from src.Exceptions import UnvalidIsotopePatternException


class IsotopePatternReader(object):
    def __init__(self):
        self.__file = None


    def getFile(self):
        return self.__file

    def findFile(self, settings):
        sequName, fragmentation, nrMod, modifications = settings[0], settings[1], settings[2], settings[3],
        if modifications == "" or nrMod == "0":
            self.__file = os.path.join(path, 'Fragment_lists', '_'.join((sequName, fragmentation) + '.csv'))
        else:
            self.__file = os.path.join(path, 'Fragment_lists', '_'.join((sequName, fragmentation, nrMod, modifications) +
                                                                      '.csv'))
        if os.path.isfile(self.__file):
            return True
        else:
            return False


    def addIsotopePatternFromFile(self, fragmentLibrary):
        '''
        Reads and processes isotope patterns from existing file
        :param file: file with istope patterns (in folder Fragment_lists)
        :return: void
        '''
        isotopePatternDict = dict()
        with open(self.__file, mode='r') as f:
            reader = csv.reader(self.__file)
            next(reader, None)
            isotopePattern = list()
            counter = 0
            for row in reader:
                if counter == 0:
                    name = row[0]
                    counter = 1
                if row[0] != '':
                    isotopePatternDict[name] = np.array(isotopePattern, dtype=[('mass',np.float64),('relAb', np.float64)])
                    name = row[0]
                    isotopePattern = list()
                isotopePattern.append((row[1], row[2]))
            isotopePatternDict[name] = np.array(isotopePattern, dtype=[('mass',np.float64),('relAb', np.float64)])
        for fragment in fragmentLibrary:
            if fragment.getName() not in isotopePatternDict:
                raise UnvalidIsotopePatternException(fragment.getName(),"not found in file")
            elif ((fragment.formula.calculateMonoIsotopic() - isotopePatternDict[name]['mass'][0]) > 10**(-6)):
                print(fragment.formula.calculateMonoIsotopic(), isotopePatternDict[name]['mass'][0])
                raise UnvalidIsotopePatternException(fragment.getName(), "monoisotopic not correct" +
                     str(fragment.formula.calculateMonoIsotopic())+ " != " + str(isotopePatternDict[name]['mass'][0]))
            fragment.isotopePattern = isotopePatternDict[fragment.getName()]
        return fragmentLibrary


    def saveIsotopePattern(self, fragmentLibrary):
        '''
        Saves calculated isotope patterns to a file
        :param file: csv-file in folder Fragment_lists
        :return: void
        '''
        np.set_printoptions(suppress=True)
        #M_max = 0
        fieldnames = ['ion', 'mass', 'Intensities']
        with open(self.__file, mode="w") as f:
            f_writer = csv.DictWriter(self.__file, fieldnames=fieldnames)
            f_writer.writeheader()
            for fragment in fragmentLibrary:
                counter = 0  # for new rows
                for isotope in fragment.isotopePattern:
                    if counter == 0:
                        #if M_max < isotope[0]:
                            #M_max = isotope[0]
                        #print(isotope[0])
                        f_writer.writerow({'ion': fragment.getName(), 'mass': np.around(isotope['mass'], 6),
                                           'Intensities': np.around(isotope['relAb'], 7)})
                        counter += 1
                    else:
                        f_writer.writerow({'ion': '', 'mass': np.around(isotope['mass'], 6),
                                           'Intensities': np.around(isotope['relAb'], 7)})


'''def __init__(self):
        self._conn = sqlite3.connect(join(path,"src","data","isoPatterns.db"))

    def makeTable(self):
        def makeTables(self):
            self._conn.cursor().execute("""
                        CREATE TABLE IF NOT EXISTS files (
                            "id"	integer PRIMARY KEY UNIQUE ,
                            "sequName"	text NOT NULL,   
                            "nrMod" integer NOT NULL ,
                            "fragName"	text NOT NULL,
                            "modName" text NOT NULL ,);""")
            self._conn.cursor().execute("""
                CREATE TABLE IF NOT EXISTS fragments (
                    "id"	integer PRIMARY KEY UNIQUE ,
                    "name"	text NOT NULL,
                    "fileId" text NOT NULL );""")
            self._conn.cursor().execute("""
                CREATE TABLE IF NOT EXISTS fragments (
                    "id"	integer PRIMARY KEY UNIQUE ,
                    "m/z"	 real NULL,
                    "relAb"	 real NULL,
                    "fragmentId" text NOT NULL );""")

    def create(self, sequence, nrMod, fragName, modName, fragmenta):
        """

        :param args: Values of the newly created item
        :return:
        """
        cur = self._conn.cursor()
        #if len(self._columns)>1:
        sql = \''' INSERT INTO files(sequName, nrMod, fragName, modName) 
                              VALUES(?,?,?,?,?)\'''
       # else:
                                          #VALUES(\''' + (len(self._columns) * '?,')[:-1] + ')'
        #print(self._mainTable, args,sql, self._columns)
        print(sql,args)
        try:
            cur.execute(sql, args)
        except sqlite3.OperationalError:
            self.makeTables()
            cur.execute(sql, args)
        self._conn.commit()
        return cur.lastrowid


    def getFragment(self):'''