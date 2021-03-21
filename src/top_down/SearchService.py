from copy import deepcopy
from datetime import datetime

from src.MolecularFormula import MolecularFormula
from src.entities.AbstractEntities import AbstractItem1
from src.entities.Search import Search
from src.repositories.SearchRepository import SearchRepository


class SearchService(object):
    def __init__(self):
        self._rep = SearchRepository()
        self._search = None

    def getAllSearchNames(self):
        return self._rep.getAllNames()

    def getSearch(self, name):
        search =self._rep.getSearch(name)
        ions = [self.ionFromDB(ion) for ion in search.getIons()]
        deletedIons = [self.ionFromDB(ion) for ion in search.getDeletedIons()]
        remIons = [self.ionFromDB(ion) for ion in search.getRemIons()]
        searchedZStates = {frag: zsString.split(',') for frag,zsString in search.getSearchedZStates().items()}
        return search.getSettings(), ions, deletedIons, remIons, searchedZStates, search.getInfo()


    def saveSearch(self, name, settings, ions, deletedIons, remIons, searchedZStates, info):
        ions = [self.ionToDB(ion) for ion in ions]
        deletedIons = [self.ionToDB(ion) for ion in deletedIons]
        remIons = [self.ionToDB(ion) for ion in remIons]
        searchedZStates = {frag: ','.join([str(z) for z in zs]) for frag,zs in searchedZStates.items()}
        search = Search([None,name, datetime.now().strftime("%d/%m/%Y %H:%M")]+ list(settings.values()),
                        ions, deletedIons, remIons, searchedZStates, info)
        if name in self._rep.getAllNames():
            self._rep.updateSearch(search)
        else:
            self._rep.createSearch(search)

    def ionFromDB(self, ion):
        ion.sequence = ion.sequence.split(',')
        ion.formula = MolecularFormula(AbstractItem1.stringToFormula2(ion.formula, {}, 1))
        return ion

    def ionToDB(self, ion):
        #print(ion.getName(), ion.formula)
        processedIon = deepcopy(ion)
        processedIon.sequence = ','.join(ion.sequence)
        processedIon.formula = ion.formula.toString()
        return processedIon

    def deleteSearch(self, name):
        self._rep.delete(name)