'''
Created on 15 Aug 2020

@author: michael
'''
import sqlite3
from os.path import join

from src.entities.GeneralEntities import Sequence
from src.repositories.sql.AbstractRepositories import AbstractRepository
from src.Exceptions import AlreadyPresentException


class SequenceRepository(AbstractRepository):
    '''
    Repository for sequences
    '''
    def __init__(self):
        super(SequenceRepository, self).__init__(join('shared.db'), 'sequences', ('name', 'sequenceList', 'molecule'), (),())

    def makeTables(self):
        self._conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS sequences (
                "id"	integer PRIMARY KEY UNIQUE ,
                "name"	text NOT NULL UNIQUE,
                "sequenceList" text NOT NULL ,
                "molecule" text NOT NULL );""")

    def createSequence(self, sequence):
        '''
        Creates an entry
        :param (Sequence) sequence: sequence object
        :raises AlreadyPresentException: if sequence name is already allocated
        '''
        try:
            self.create((sequence.getName(), sequence.getSequenceString(), sequence.getMolecule()))
        except sqlite3.IntegrityError:
            raise AlreadyPresentException(sequence.getName())

    def getSequence(self, name):
        '''
        Returns sequence with the stated name in the database
        :param (str) name: name of the sequence
        :return: (Sequence) sequence
        '''
        sequenceTuple = self.get('name', name)
        return Sequence(sequenceTuple[1], sequenceTuple[2], sequenceTuple[3], sequenceTuple[0])

    def getAllSequences(self):
        '''
        Returns all sequence values in database as tuples
        :return: (list[tuple[str, str, str]])
        '''
        sequences = []
        for sequenceTuple in self.getAll():
            sequences.append((sequenceTuple[1], sequenceTuple[2], sequenceTuple[3]))
        return sequences


    def getAllSequencesAsObjects(self):
        '''
        Returns all sequence values in database as Sequence objects
        :return: (list[Sequence]) sequences
        '''
        sequences = []
        for sequenceTuple in self.getAll():
            sequences.append(Sequence(sequenceTuple[1], sequenceTuple[2], sequenceTuple[3], sequenceTuple[4]))
        return sequences


    def getAllSequenceNames(self):
        '''
        Returns all sequence names in database
        :return: (list[str]) names
        '''
        sequenceNames = []
        for sequenceTuple in self.getAll():
            sequenceNames.append(sequenceTuple[1])
        return sequenceNames


    def getItemColumns(self):
        '''
        Returns the column names and corresponding tooltips for the user
        :return: (dict[str,str]) dictionary of {column name: tooltip}
        '''
        return {"Name": "Enter the name for the sequenceList",
                "Sequence":"Enter the sequenceList (no Spaces allowed)", "Molecule":"Enter the type of Molecule"}



    def updateSequence(self, sequence):
        '''
        Updates an entry in the database
        :param (Sequence) sequence: sequence to update
        '''
        #self.update(sequenceList.getName(), sequenceList.getSequenceString(), sequenceList.getMolecule(), sequenceList.getId())
        cur = self._conn.cursor()
        sql = 'UPDATE sequences SET ' + '=?, '.join(self._columns) + '=? WHERE name=?'
        cur.execute(sql, (sequence.getName(), sequence.getSequenceString(), sequence.getMolecule(), sequence.getName()))
        self._conn.commit()


    """def deleteSequence(self):
        pass"""
