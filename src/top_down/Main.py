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
#from src.views.ParameterDialogs import TDStartDialog
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
class TD_MainController(object):
    def __init__(self, parrent):
        self.mainWindow = parrent

    def run(self):
        settings = ConfigurationHandlerFactory.getTD_SettingHandler().getAll()
        configs = ConfigurationHandlerFactory.getTD_ConfigHandler().getAll()

        print("\n********** Creating fragment library **********")
        libraryBuilder = FragmentLibraryBuilder(settings['sequName'], settings['fragmentation'],
                        settings['modifications'], settings['nrMod'])
        libraryBuilder.createFragmentLibrary()

        """read existing ion-list file or create new one"""
        libraryImported = False
        patternReader = IsotopePatternReader()
        if (patternReader.findFile([settings[setting] for setting in ['sequName','fragmentation', 'nrMod',
                                                                            'modifications']])):
            print("\n********** Importing list of isotope patterns from:", patternReader.getFile(), "**********")
            try:
                libraryBuilder.setFragmentLibrary(patternReader)
                libraryImported = True
                print("done")
            except UnvalidIsotopePatternException:
                traceback.print_exc()
                choice = QtWidgets.QMessageBox.question(self.mainWindow, "Problem with importing list of isotope patterns",
                        "Imported Fragment Library from" + patternReader.getFile() + "incomplete\n"
                        "Should a new library be created?\nThe search will be stopped otherwise",
                                                        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                if choice != QtWidgets.QMessageBox.Yes:
                    return
                    #sys.exit()
        if libraryImported == False:
            print("\n********** Writing new list of isotope patterns to:", patternReader.getFile(), "**********\n")
            start = time.time()
            patternReader.saveIsotopePattern(libraryBuilder.addNewIsotopePattern())
            print("\ndone\nexecution time: ", round((time.time() - start) / 60, 2), "min\n")

        #ToDo
        """Importing spectral pattern"""
        if settings['spectralData'] == '':
            return
        spectralFile = os.path.join(path, 'Spectral_data','top-down', settings['spectralData'])
        print("\n********** Importing spectral pattern from:", spectralFile, "**********")
        spectrumHandler = SpectrumHandler(spectralFile, libraryBuilder.getSequence(), libraryBuilder.getFragmentLibrary(),
                libraryBuilder.getPrecursor(), libraryBuilder.getChargedModifications(), settings)

        """Finding fragments"""
        print("\n********** Search for spectrum **********")
        start = time.time()
        spectrumHandler.findPeaks()
        print("\ndone\nexecution time: ", round((time.time() - start) / 60, 3), "min\n")

        intensityModeller = IntensityModeller(configs)
        start = time.time()
        print("\n********** Calculating relative abundances **********")
        for ion in spectrumHandler.foundIons:
            intensityModeller.processIons(ion)
        for ion in spectrumHandler.ionsInNoise:
            intensityModeller.processNoiseIons(ion)
        print("\ndone\nexecution time: ", round((time.time() - start) / 60, 3), "min\n")

        """Handle spectrum with same monoisotopic peak and charge"""
        print("\n********** Handling overlaps **********")
        sameMonoisotopics = intensityModeller.findSameMonoisotopics()
        if len(sameMonoisotopics) > 0:
            view = CheckMonoisotopicOverlapView(sameMonoisotopics)
            view.exec_()
            if view and not view.canceled:
                intensityModeller.deleteSameMonoisotopics(view.getDumplist())
            else:
                return

        """remodelling overlaps"""
        print("\n********** Re-modelling overlaps **********")
        counter = 0
        while True:
            complexPatterns = intensityModeller.findOverlaps()
            if len(complexPatterns) > 0:
                view = CheckOverlapsView(complexPatterns)
                view.exec_()
                if view and not view.canceled:
                    intensityModeller.remodelComplexPatterns(complexPatterns, view.getDumplist())
                else:
                    return
            if counter > 0:
                break
            view = FinalIonView(list(intensityModeller.correctedIons.values()))
            view.exec_()
            if view and not view.canceled:
                if len(view.getDumplist())>0:
                    intensityModeller.deleteIons(view.getDumplist())
                    counter +=1
                else:
                    break
            else:
                return

        """analysis"""
        analyser = Analyser(list(intensityModeller.correctedIons.values()), libraryBuilder.getSequence().getSequenceList(),
                        settings['charge'], libraryBuilder.getModification())

        """output"""
        output = settings.get('output')
        if output == '':
            output = spectralFile[0:-4] + '_out' + '.xlsx'
        else:
            output = os.path.join(path, 'Spectral_data','top-down', output + '.xlsx')
        excelWriter = ExcelWriter(output, configs)

        try:
            generalParam = [("spectralFile:", spectralFile),
                            ('date:', ""),
                            ('noiseLimit:', settings['noiseLimit']),
                            ('max m/z:',spectrumHandler.getUpperBound())]
            #percentages = list()
            excelWriter.writeAnalysis(generalParam,
                                      analyser.getModificationLoss(),
                                      analyser.calculateRelAbundanceOfSpecies(),
                                      libraryBuilder.getSequence().getSequenceList(),
                                      analyser.calculatePercentages(configs['interestingIons']))
            #analyser.createPlot(__maxMod)
            precursorRegion = intensityModeller.getPrecRegion(settings['sequName'], abs(settings['charge']))
            excelWriter.writeIons(excelWriter.worksheet2, intensityModeller.correctedIons.values(),
                                  precursorRegion)
            excelWriter.writePeaks(excelWriter.worksheet3,0,0,intensityModeller.correctedIons.values())
            row = excelWriter.writeIons(excelWriter.worksheet4, sortIonsByName(intensityModeller.deletedIons),
                                  precursorRegion)
            excelWriter.writePeaks(excelWriter.worksheet4,row+3,0,sortIonsByName(intensityModeller.deletedIons))
            excelWriter.writeIons(excelWriter.worksheet5, sortIonsByName(intensityModeller.remodelledIons),
                                  precursorRegion)
            excelWriter.writeSumFormulas(libraryBuilder.getFragmentLibrary(), spectrumHandler.searchedChargeStates)
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
    TD_MainController(gui).run()
    sys.exit(app.exec_())"""