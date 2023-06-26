from copy import deepcopy
from datetime import datetime

from src.services.MolecularFormula import MolecularFormula
from src.services.FormulaFunctions import stringToFormula2
from src.entities.Search import Search
from src.repositories.sql.SearchRepository import SearchRepository
from src.services.IntensityModeller import calcScore


class SearchService(object):
    '''
    Service handling a SearchRepository and Search entities.
    '''
    def __init__(self):
        self._rep = SearchRepository()
        self._search = None

    def getAllSearchNames(self):
        return self._rep.getAllNames()

    def getSearch(self, name):
        '''
        Returns the values of a stored analysis
        :param (str) name: name of the analysis/search
        :return: (tuple[dict[str,Any], list[FragmentIon], list[FragmentIon], list[FragmentIon], dict[str, list[int]],
            str) settings {name:value}, observed ions, deleted ions, remodelled ions, calculated charge states per
            fragment {fragment name: charge states}, information log
        '''
        search =self._rep.getSearch(name)
        if search.getNoiseLevel() == 0:
            search.setNoiseLevel(search.getSettings()['noiseLimit'])
        noiseLevel = search.getNoiseLevel()
        ions = [self.ionFromDB(ion, noiseLevel) for ion in search.getIons()]
        deletedIons = [self.ionFromDB(ion, noiseLevel) for ion in search.getDeletedIons()]
        remIons = [self.ionFromDB(ion, noiseLevel) for ion in search.getRemIons()]
        searchedZStates = {frag: zsString.split(',') for frag,zsString in search.getSearchedZStates().items()}
        return search.getSettings(), search.getNoiseLevel(), ions, deletedIons, remIons, searchedZStates, search.getInfo()


    def saveSearch(self, name, noiseLevel, settings, ions, deletedIons, remIons, searchedZStates, info):
        '''
        Saves or updates a search/analysis
        :param (str) name: name of the search/analysis
        :param (dict[str,Any]) settings: settings
        :param (list[FragmentIon]) ions: observed ions
        :param (list[FragmentIon]) deletedIons: deleted ions
        :param (list[FragmentIon]) remIons: remodelled ions
        :param (dict[str, list[int]]) searchedZStates: calculated charge states per fragment
        :param (Info) info: information log
        '''
        ions = [self.ionToDB(ion) for ion in ions]
        deletedIons = [self.ionToDB(ion) for ion in deletedIons]
        remIons = [self.ionToDB(ion) for ion in remIons]
        searchedZStates = {frag: ','.join([str(z) for z in zs]) for frag,zs in searchedZStates.items()}
        search = Search([None,name, datetime.now().strftime("%d/%m/%Y %H:%M"), int(noiseLevel)]+ list(settings.values()),
                        ions, deletedIons, remIons, searchedZStates, info)
        if name in self._rep.getAllNames():
            self._rep.updateSearch(search)
        else:
            self._rep.createSearch(search)


    def ionFromDB(self, ion, noiseLevel):
        '''
        Processes the sequence and the formula of an ion which was read from the database
        :param (FragmentIon) ion: ion with strings as sequence and formula
        :return: (FragmentIon) ion with list[str] as sequence and MolecularFormula as formula
        '''
        #ion.setSequence(ion.getSequence().split(','))
        ion.setFormula(MolecularFormula(stringToFormula2(ion.getFormula(), {}, 1)))
        ion.setScore(calcScore(ion.getIntensity(), ion.getQuality(), noiseLevel))
        return ion

    def ionToDB(self, ion):
        '''
        Processes the sequence and the formula of an ion to save it in the database
        :param (FragmentIon) ion: ion with list[str] as sequence and MolecularFormula as formula
        :return: (FragmentIon) ion with strings as sequence and formula
        '''
        #print(ion.getName(), ion.formula)
        processedIon = deepcopy(ion)
        #processedIon.setSequence(','.join(ion.getSequence()))
        processedIon.setFormula(ion.getFormula().toString())
        return processedIon

    def deleteSearch(self, name):
        self._rep.delete(name)

    @staticmethod
    def getAllAssignedPeaks(ions):
        peaks = set()
        for ion in ions:
            peaks.update({(peak['m/z'],peak['I']) for peak in ion.getIsotopePattern() if peak['I']!=0})
        return peaks