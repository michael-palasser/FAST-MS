'''
Created on 15 Aug 2020

@author: michael
'''
import sqlite3
from re import findall

from src.Entities.GeneralEntities import Sequence
from src.Repositories.AbstractRepositories import AbstractRepository
from src.Exceptions import AlreadyPresentException


class SequenceRepository(AbstractRepository):
    def __init__(self):
        super(SequenceRepository, self).__init__('Shared_data.db', 'sequences', ('name', 'sequence', 'molecule'), (),())

    def makeTables(self):
        self._conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS sequences (
                "id"	integer PRIMARY KEY UNIQUE ,
                "name"	text NOT NULL UNIQUE,
                "sequence" text NOT NULL ,
                "molecule" text NOT NULL );""")

    def addSequence(self, sequence):
        try:
            self.create(sequence.getName(), sequence.getSequence(), sequence.getMolecule())
        except sqlite3.IntegrityError:
            raise AlreadyPresentException(sequence.getName())

    def getSequence(self, name):
        sequenceTuple = self.get('name', name)
        return Sequence(sequenceTuple[1], sequenceTuple[2], sequenceTuple[3], sequenceTuple[4])

    def getAllSequences(self):
        sequences = []
        for sequenceTuple in self.getAll():
            sequences.append((sequenceTuple[1], sequenceTuple[2], sequenceTuple[3], sequenceTuple[4]))
        return sequences

    def getAllSequenceNames(self):
        sequenceNames = []
        for sequenceTuple in self.getAll():
            sequenceNames.append(sequenceTuple[1])
        return sequenceNames


    def getItemColumns(self):
        return {"Name": "Enter the name for the sequence",
                "Sequence":"Enter the sequence (no Spaces allowed)", "Molecule":"Enter the type of Molecule"}

    def getAllSequencesAsObjects(self):
        sequences = []
        for sequenceTuple in self.getAll():
            sequences.append(Sequence(sequenceTuple[1], sequenceTuple[2], sequenceTuple[3], sequenceTuple[4]))
        return sequences

    def createSequence(self, sequence):
        self.create(sequence.getName(),sequence.getSequence(),sequence.getMolecule())

    def updateSequence(self, sequence):
        self.update(sequence.getName(), sequence.getSequence(), sequence.getMolecule(), sequence.getId())
        cur = self._conn.cursor()
        sql = 'UPDATE sequence SET ' + '=?, '.join(self._columns) + '=? WHERE name=?'
        cur.execute(sql, sequence[0], sequence[1], sequence[2])
        self._conn.commit()


    """def deleteSequence(self):
        pass"""
