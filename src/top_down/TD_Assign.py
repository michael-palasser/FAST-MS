import os

from src.entities.SearchSettings import SearchSettings
from src.repositories.ConfigurationHandler import ConfigurationHandlerFactory
from src.resources import path
from src.services.assign_services.AbstractSpectrumHandler import calculateError, getMz
from src.services.assign_services.Finders import TD_Finder
from src.services.library_services.FragmentLibraryBuilder import FragmentLibraryBuilder
from src.top_down.PeakMatcher import PeakMatcher
from src.repositories.SpectralDataReader import SpectralDataReader
from src.top_down.EvaluationWriter import *


class TD_Assigner(object):
    def __init__(self, settings):
        self._allSettings = dict(settings)
        self._allSettings.update(ConfigurationHandlerFactory().getConfigHandler().getAll())
        self._propStorage = SearchSettings(settings['sequName'], settings['fragmentation'], settings['modifications'])

    def search(self, peakSearch=True):
        '''
        Search for ions in spectrum: Calculates theo. isotope patterns, searches for these in the spectrum (peak list),
        models intensities, fixes problems by overlapping ions (2 user inputs possible for deleting ions)
        '''
        print("\n********** Creating fragment library **********")
        libraryBuilder = FragmentLibraryBuilder(self._propStorage, self._allSettings['nrMod'], 0.5, 2)
        libraryBuilder.createFragmentLibrary()
        libraryBuilder.addNewIsotopePattern()#ld.progress))
        print("done")

        print("\n********** Search for ions **********")
        reader = SpectralDataReader()
        ionData = reader.openFile(self._allSettings['snapData'],
                                  np.dtype([('m/z', float), ('z', np.uint8), ('I', float), ('S/N', float),
                                               ('qual', float)]))
        finder = TD_Finder(libraryBuilder.getFragmentLibrary(), self._allSettings, self.getChargeRange)
        assignedIons = finder.findIonsInSpectrum(0, self._allSettings['errorlimit'], ionData)
        print("done")

        if peakSearch:
            print("\n********** Matching with Peak Data **********")
            peakDtype = np.dtype([('m/z', float), ('I', float), ('S/N', float)])
            peakData = reader.openFile(self._allSettings['peakData'], peakDtype)
            peakMatcher = PeakMatcher(self._allSettings['errorlimit'], peakDtype)
            assignedIons, overlapList = peakMatcher.matchPeaks(assignedIons, peakData)
            ionArray = self.makeArray(assignedIons)
            sequLength  = len(self._propStorage.getSequenceList())
            precursor = libraryBuilder.getPrecursor()
            evaluater = EvaluationWriter(sequLength,abs(getMz(precursor.getMonoisotopicMass(),self._allSettings['charge'],
                                                              precursor.getRadicals())))
            analysisForward = self.analyseData(sequLength, ionArray, forwardTypes)

            analysisBack = self.analyseData(sequLength, ionArray, backwardTypes)
            #try:
            #formatedIons = [formatVals(ion, (-5, -4)) for ion in ionArray]
            evaluater.makeOutput(os.path.join(path,'Spectral_data','Output.xlsx'), self._allSettings, ionArray, analysisForward,
                                     analysisBack, overlapList)
            #except:
            #    print('Permission denied. Please close the file "output.xlsx" before running the script!')
                #traceback.print_exc()

    def getChargeRange(self, *args):
        return range(1,abs(self._allSettings['charge'])+1)

    @staticmethod
    def analyseData(sequLength, data, direction):
        bestIons, secondIons = [], []
        for i in range(1, sequLength):
            current = data[np.where(np.isin(data['type'], direction) & (data['number'] == i))]
            length = len(current)
            if length == 0:
                bestIons.append(formatVals([]))
                secondIons.append(formatVals([]))
            elif length == 1:
                bestIons.append(formatVals(current[0]))
                secondIons.append(formatVals([]))
            else:
                '''current = np.sort(current, order='S/N_SNAP')
                bestIons.append(formatVals(current[-1]))
                secondIons.append(formatVals(current[-2]))'''
                current = np.sort(current, order='S/N_SNAP')
                best = current[-1]
                bestIons.append(formatVals(best))
                current = np.sort(current, order='mono_S/N')
                if (current[-1]['name'] != best['name']) or (current[-1]['charge'] != best['charge']):
                    secondIons.append(formatVals(current[-1]))
                else:
                    secondIons.append(formatVals(current[-2]))
        return bestIons, secondIons

    @staticmethod
    def makeArray(ions):
        ionList = []
        for ion in ions:
            monoisotopic = ion.getMonoPeak()
            ionList.append((ion.getMonoisotopic(), ion.getCharge(), ion.getName(), ion.getTheoMz(), np.around(ion.getError(),2),
                            ion.getIntensity(), ion.getSNR(),
                            ion.getQual(), ion.getType(), ion.getNumber(), monoisotopic['m/z'], monoisotopic['S/N'],
                            np.around(calculateError(monoisotopic['m/z'], ion.getTheoMz()),2)))
        return np.array(ionList,dtype=ionDType)


#ToDo: Array zu Objekt oder umgekehrt