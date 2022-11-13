import numpy as np

from src.entities.SearchSettings import SearchSettings
from src.resources import path
from src.services.assign_services.Finders import TD_Finder
from src.services.library_services.FragmentLibraryBuilder import FragmentLibraryBuilder
from src.top_down.PeakMatcher import PeakMatcher


class TD_Assigner(object):
    def __init__(self, settings, configs):
        self._allSettings = dict(settings)
        self._allSettings.update(configs)
        self._propStorage = SearchSettings(settings['sequName'], settings['fragmentation'], settings['modifications'])
        self.search()

    def search(self):
        '''
        Search for ions in spectrum: Calculates theo. isotope patterns, searches for these in the spectrum (peak list),
        models intensities, fixes problems by overlapping ions (2 user inputs possible for deleting ions)
        '''
        print("\n********** Creating fragment library **********")
        self._libraryBuilder = FragmentLibraryBuilder(self._propStorage, self._allSettings['nrMod'], 0.5, 2)
        self._libraryBuilder.createFragmentLibrary()
        self._libraryBuilder.addNewIsotopePattern()#ld.progress))
        print("done")

        print("\n********** Search for ions **********")
        self._finder = TD_Finder(self._libraryBuilder.getFragmentLibrary(), self._allSettings, self.getChargeRange)
        self._ionData = self._finder.readFile(self._allSettings['spectralData'])[0]
        self._assignedIons = self._finder.findIonsInSpectrum(0, self._allSettings['errorlimit'], self._ionData)
        print("done")
        print("\n********** Matching with Peak Data **********")
        peakData = self.openPeakList(self._allSettings['peakData'])
        peakMatcher = PeakMatcher(self._allSettings['errorlimit:'])
        self._ionData, overlapList = peakMatcher.matchPeaks(self._ionData, peakData)
        return self._assignedIons

    def getChargeRange(self, *args):
        return range(1,abs(self._allSettings['charge'])+1)

    def openPeakList(absolutePath):
        data = []
        # absolutePath = 'input'
        with open(absolutePath, 'r') as f:
            for i, line in enumerate(f):
                strippedLine = line.rstrip()
                if i > 0:
                    items = strippedLine.split()
                    data.append((items[1], items[4]))
        '''if len(data[0]) != 2:
            raise Exception('Incorrect number of columns')'''
        dataArray = np.array(data, dtype=float)
        return dataArray

    def analyse(self):
        pass

    def export(self):
        pass

    def getIonData(self):
        return self._ionData
    def getFinder(self):
        return self._finder

#ToDo: SNAP Data correct einlesen
#ToDo: Array zu Objekt oder umgekehrt