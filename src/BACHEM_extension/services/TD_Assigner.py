from datetime import datetime
import os
import numpy as np

from src.entities.SearchSettings import SearchSettings
from src.repositories.ConfigurationHandler import ConfigurationHandlerFactory
from src.resources import autoStart, path
from src.services.assign_services.AbstractSpectrumHandler import calculateError, getMz
from src.services.assign_services.Finders import TD_Finder
from src.services.library_services.FragmentLibraryBuilder import FragmentLibraryBuilder
from src.BACHEM_extension.services.MD_analyser import MD_Analyser,ionDType
from src.BACHEM_extension.services.PeakMatcher import PeakMatcher
from src.repositories.SpectralDataReader import SpectralDataReader
from src.BACHEM_extension.services.EvaluationWriter import EvaluationWriter

peakDtype = np.dtype([('m/z', float), ('I', float), ('S/N', float)])
snapDtype = np.dtype([('m/z', float), ('z', np.uint8), ('I', float), ('S/N', float),('qual', float)])

def makeArray(ions):
    ionList = []
    for ion in ions:
        monoisotopic = ion.getMonoPeak()
        ionList.append((ion.getMonoisotopic(), ion.getCharge(), ion.getName(), ion.getTheoMz(), np.around(ion.getError(),2),
                        ion.getIntensity(), ion.getSNR(),
                        ion.getQual(), ion.getType(), ion.getNumber(), monoisotopic['m/z'], monoisotopic['S/N'],
                        np.around(calculateError(monoisotopic['m/z'], ion.getTheoMz()),2)))
    return np.array(ionList,dtype=ionDType)




class TD_Assigner(object):
    """
    Class that controls the analysis of MSMS MD analysis of SNAP and SumPeak lists. Depricated functionality
    """
    def __init__(self):
        self._allSettings = ConfigurationHandlerFactory.getMDHandler().getAll()
        self._allSettings.update(ConfigurationHandlerFactory().getConfigHandler().getAll())
        self._propStorage = SearchSettings(self._allSettings['sequName'], self._allSettings['fragmentation'], self._allSettings['modifications'])


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
        ionData = reader.openFile(self._allSettings['snapData'], snapDtype)
        finder = TD_Finder(libraryBuilder.getFragmentLibrary(), self._allSettings, self.getChargeRange)
        assignedIons = finder.findIonsInSpectrum(self._allSettings['k'], self._allSettings['d'], ionData)
        print("done")

        if peakSearch:
            print("\n********** Matching with Peak Data **********")
            peakData = reader.openFile(self._allSettings['spectralData'], peakDtype)
            peakMatcher = PeakMatcher(self._allSettings['k'], self._allSettings['d'], peakDtype)
            assignedIons, overlapList = peakMatcher.matchPeaks(assignedIons, peakData)
            print("done")
            print("\n********** Analysing Data **********")
            ionArray = makeArray(assignedIons)
            sequLength  = len(self._propStorage.getSequenceList())
            precursor = libraryBuilder.getPrecursor()
            analyser = MD_Analyser(sequLength)
            analysisForward = analyser.analyseData(ionArray)
            analysisBack = analyser.analyseData(ionArray, False)
            best = analyser.takeBest(analysisForward[0], analysisBack[0])
            print("done")
            writer = EvaluationWriter(sequLength,abs(getMz(precursor.getMonoisotopicMass(),self._allSettings['charge'],
                                                              precursor.getRadicals())))
            #try:
            #formatedIons = [formatVals(ion, (-5, -4)) for ion in ionArray]
            output = self._allSettings["output"]
            if output == '':
                output =  self._allSettings['spectralData'][:-5] + "_" + datetime.now().strftime("%d.%m.%Y") + ".xlsx"
            else:
                output =  os.path.join(path,'Spectral_data', output  + ".xlsx")
            writer.makeOutput(output, self._allSettings, ionArray, overlapList, analysisForward, analysisBack, best, self._allSettings["sequName"]) 
            autoStart(output)
            #except:
            #    print('Permission denied. Please close the file "output.xlsx" before running the script!')
                #traceback.print_exc()

    def getChargeRange(self, *args):
        return range(1,abs(self._allSettings['charge'])+1)

    """@staticmethod
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
        return bestIons, secondIons"""




#ToDo: Array zu Objekt oder umgekehrt