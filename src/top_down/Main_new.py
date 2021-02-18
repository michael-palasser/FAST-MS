'''
Created on 21 Jul 2020

@author: michael
'''

import os
import subprocess
import traceback
import sys
import time

from PyQt5 import QtWidgets

from src.Exceptions import UnvalidIsotopePatternException
from src.repositories.ConfigurationHandler import ConfigurationHandlerFactory
#from src.gui.ParameterDialogs import TDStartDialog
from src.repositories.IsotopePatternRepository import IsotopePatternReader
from src.top_down.Analyser import Analyser
from src.top_down.LibraryBuilder import FragmentLibraryBuilder
from src.top_down.SpectrumHandler import SpectrumHandler
from src.top_down.IntensityModeller import IntensityModeller
from src.top_down.ExcelWriter import ExcelWriter
from src import path
from src.views.CheckIonView import CheckMonoisotopicOverlapView, CheckOverlapsView, FinalIonView


def sortIonsByName(ionList):
    #return sorted(ionList,key=lambda obj:(obj.type ,obj.number))
    return sorted(ionList, key=lambda obj: (obj.getName(), obj.charge))



#if __name__ == '__main__':
class TD_Facade(object):
    def __init__(self, settings):
        self.settings = settings
        self.configs = ConfigurationHandlerFactory.getTD_ConfigHandler().getAll()

    def start(self):
        print("\n********** Creating fragment library **********")
        self.libraryBuilder = FragmentLibraryBuilder(self.settings['sequName'], self.settings['fragmentation'],
                        self.settings['modifications'], self.settings['nrMod'])
        self.libraryBuilder.createFragmentLibrary()

        """read existing ion-list file or create new one"""
        libraryImported = False
        patternReader = IsotopePatternReader()
        if (patternReader.findFile([self.settings[setting] for setting in ['sequName','fragmentation', 'nrMod',
                                                                            'modifications']])):
            print("\n********** Importing list of isotope patterns from:", patternReader.getFile(), "**********")
            try:
                self.libraryBuilder.setFragmentLibrary(patternReader)
                libraryImported = True
                print("done")
            except UnvalidIsotopePatternException:
                traceback.print_exc()
                choice = QtWidgets.QMessageBox.question(None, "Problem with importing list of isotope patterns",
                        "Imported Fragment Library from" + patternReader.getFile() + "incomplete\n"
                        "Should a new library be created?\nThe search will be stopped otherwise",
                                                        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                if choice != QtWidgets.QMessageBox.Yes:
                    return
                    #sys.exit()
        if libraryImported == False:
            print("\n********** Writing new list of isotope patterns to:", patternReader.getFile(), "**********\n")
            start = time.time()
            patternReader.saveIsotopePattern(self.libraryBuilder.addNewIsotopePattern())
            print("\ndone\nexecution time: ", round((time.time() - start) / 60, 2), "min\n")

        #ToDo
        """Importing spectral pattern"""
        if self.settings['spectralData'] == '':
            return
        #spectralFile = os.path.join(path, 'Spectral_data','top-down', self.settings['spectralData'])
        print("\n********** Importing spectral pattern from:", self.settings['spectralData'], "**********")
        self.spectrumHandler = SpectrumHandler(self.settings['spectralData'], self.libraryBuilder.getSequence(), self.libraryBuilder.getMolecule(),
                  self.libraryBuilder.getFragmentLibrary(), self.libraryBuilder.getPrecursor(),
                  self.libraryBuilder.getChargedModifications(), self.libraryBuilder.getFragItemDict(), self.settings)

        """Finding fragments"""
        print("\n********** Search for spectrum **********")
        start = time.time()
        self.spectrumHandler.findPeaks()
        print("\ndone\nexecution time: ", round((time.time() - start) / 60, 3), "min\n")

        self.intensityModeller = IntensityModeller(self.configs)
        start = time.time()
        print("\n********** Calculating relative abundances **********")
        for ion in self.spectrumHandler.foundIons:
            self.intensityModeller.processIons(ion)
        for ion in self.spectrumHandler.ionsInNoise:
            self.intensityModeller.processNoiseIons(ion)
        print("\ndone\nexecution time: ", round((time.time() - start) / 60, 3), "min\n")

    def getSpectrum(self):
        return self.spectrumHandler.getSpectrum()

    def getMonoisotopicOverlaps(self):
        """Handle spectrum with same monoisotopic peak and charge"""
        print("\n********** Handling overlaps **********")
        return self.intensityModeller.findSameMonoisotopics()

        """if len(sameMonoisotopics) > 0:
            view = CheckMonoisotopicOverlapView(sameMonoisotopics, self.spectrumHandler.getSpectrum())
            view.exec_()
            if view and not view.canceled:
                self.intensityModeller.deleteSameMonoisotopics(view.getDumplist())
            else:
                return"""

    def modelOverlaps(self):
        """remodelling overlaps"""
        print("\n********** Re-modelling overlaps **********")
        return self.intensityModeller.findOverlaps()
        """if len(complexPatterns) > 0:
            view = CheckOverlapsView(complexPatterns, self.spectrumHandler.getSpectrum())
            view.exec_()
            if view and not view.canceled:
                self.intensityModeller.remodelComplexPatterns(complexPatterns, view.getDumplist())
            else:
                return
        view = FinalIonView(list(self.intensityModeller._correctedIons.values()), self.spectrumHandler.getSpectrum())
        view.exec_()
        if view and not view.canceled:
            if len(view.getDumplist())>0:
                self.intensityModeller.deleteIons(view.getDumplist())
            else:
                break
        else:
            return"""

    def remodelComplexOverlaps(self, complexPatterns, dumpList):
        self.intensityModeller.remodelComplexPatterns(complexPatterns, dumpList)
        return self.intensityModeller._correctedIons

    def getSpectrum(self, minLimit, maxLimit):
        return self._spectrum[np.where((self._spectrum[:,0]>(minLimit)) & (self._spectrum[:,0]<(maxLimit)))]

        #"""analysis"""
        #self.analyser = Analyser(list(self.intensityModeller._correctedIons.values()), self.libraryBuilder.getSequence().getSequenceList(),
                        #self.settings['charge'], self.libraryBuilder.getModification())

    def toExcel(self): #ToDo
        """output"""
        output = self.settings.get('output')
        if output == '':
            output = self.settings['spectralData'][0:-4] + '_out' + '.xlsx'
        else:
            output = os.path.join(path, 'Spectral_data','top-down', output + '.xlsx')
        excelWriter = ExcelWriter(output, self.configs)

        try:
            generalParam = [("spectralFile:", self.settings['spectralData']),
                            ('date:', ""),
                            ('noiseLimit:', self.settings['noiseLimit']),
                            ('max m/z:',self.spectrumHandler.getUpperBound())]
            #percentages = list()
            excelWriter.writeAnalysis(generalParam,
                                      self.analyser.getModificationLoss(),
                                      self.analyser.calculateRelAbundanceOfSpecies(),
                                      self.libraryBuilder.getSequence().getSequenceList(),
                                      self.analyser.calculatePercentages(self.configs['interestingIons']))
            #self.analyser.createPlot(__maxMod)
            precursorRegion = self.intensityModeller.getPrecRegion(self.settings['sequName'], abs(self.settings['charge']))
            excelWriter.writeIons(excelWriter.worksheet2, self.intensityModeller._correctedIons.values(),
                                  precursorRegion)
            excelWriter.writePeaks(excelWriter.worksheet3, 0, 0, self.intensityModeller._correctedIons.values())
            row = excelWriter.writeIons(excelWriter.worksheet4, sortIonsByName(self.intensityModeller._deletedIons),
                                        precursorRegion)
            excelWriter.writePeaks(excelWriter.worksheet4, row + 3, 0, sortIonsByName(self.intensityModeller._deletedIons))
            excelWriter.writeIons(excelWriter.worksheet5, sortIonsByName(self.intensityModeller._remodelledIons),
                                  precursorRegion)
            excelWriter.writeSumFormulas(self.libraryBuilder.getFragmentLibrary(), self.spectrumHandler.searchedChargeStates)
            print("********** saved in:", output, "**********\n")
        finally:
            excelWriter.closeWorkbook()
        try:
            subprocess.call(['open',output])
        except:
            pass
        return 0


"""if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = Window()
    TD_Facade(gui).run()
    sys.exit(app.exec_())"""