'''
Created on 15 Aug 2020

@author: michael
'''
import sqlite3
from os.path import join

from src.entities.GeneralEntities import Sequence
from src.repositories.AbstractRepositories import AbstractRepository
from src.Exceptions import AlreadyPresentException


class SequenceRepository(AbstractRepository):
    def __init__(self):
        super(SequenceRepository, self).__init__(join('shared.db'), 'sequences', ('name', 'sequence', 'molecule'), (),())

    def makeTables(self):
        self._conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS sequences (
                "id"	integer PRIMARY KEY UNIQUE ,
                "name"	text NOT NULL UNIQUE,
                "sequence" text NOT NULL ,
                "molecule" text NOT NULL );""")

    def createSequence(self, sequence):
        try:
            self.create(sequence.getName(), sequence.getSequenceString(), sequence.getMolecule())
        except sqlite3.IntegrityError:
            raise AlreadyPresentException(sequence.getName())

    def getSequence(self, name):
        sequenceTuple = self.get('name', name)
        return Sequence(sequenceTuple[1], sequenceTuple[2], sequenceTuple[3], sequenceTuple[0])

    def getAllSequences(self):
        sequences = []
        for sequenceTuple in self.getAll():
            print(sequenceTuple)
            sequences.append((sequenceTuple[1], sequenceTuple[2], sequenceTuple[3]))
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


    def updateSequence(self, sequence):
        #self.update(sequence.getName(), sequence.getSequenceString(), sequence.getMolecule(), sequence.getId())
        cur = self._conn.cursor()
        sql = 'UPDATE sequences SET ' + '=?, '.join(self._columns) + '=? WHERE name=?'
        cur.execute(sql, (sequence.getName(), sequence.getSequenceString(), sequence.getMolecule(), sequence.getName()))
        self._conn.commit()


    """def deleteSequence(self):
        pass"""
