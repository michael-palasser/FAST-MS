'''
Created on 21 Jul 2020

@author: michael
'''
import traceback
import os
from datetime import datetime

import time
from PyQt5 import QtWidgets

from src.resources import path, autoStart
from src.Exceptions import InvalidInputException
from src.services.DataServices import IntactIonService, SequenceService
from src.entities.Info import Info
from src.entities.IonTemplates import IntactModification
from src.gui.controller.AbstractController import AbstractMainController
from src.services.analyser_services.IntactAnalyser import IntactAnalyser
from src.repositories.export.IntactExcelWriter import FullIntactExcelWriter
from src.services.assign_services.Calibrator import Calibrator
from src.services.library_services.IntactLibraryBuilder import IntactLibraryBuilder
from src.services.assign_services.IntactSpectrumHandler import IntactSpectrumHandler
from src.repositories.ConfigurationHandler import ConfigurationHandlerFactory
from src.services.IntensityModeller import IntensityModeller
from src.gui.dialogs.CheckIonView import CheckMonoisotopicOverlapView
from src.gui.dialogs.SimpleDialogs import ExportDialog
from src.gui.dialogs.StartDialogs import IntactStartDialogFull



class IntactMainController(AbstractMainController):
    '''
    Controller class for starting, saving, exporting and loading a top-down search/analysis
    '''
    def __init__(self, parent, new, window):
        '''
        Starts either the search or loads a search from the database. Afterwards, result windows are shown.
        :param parent:
        :param (bool) new: True if new search, False if old search is loaded
        '''
        super(IntactMainController, self).__init__(window)
        #self._mainWindow= window
        #if new:
        dialog = IntactStartDialogFull(parent)
        dialog.exec_()
        if dialog.canceled():
            return
        self._settings = dialog.newSettings()
        self._configs = ConfigurationHandlerFactory.getConfigHandler().getAll()
        #self._propStorage = IntactSearchSettings(self._settings['sequName'], self._settings['modifications'])
        self._sequence = SequenceService().get(self._settings['sequName'])
        modification = IntactIonService().getPatternWithObjects(self._settings['modifications'], IntactModification)
        self._info = Info(self._settings, self._configs, self._sequence.getSequenceList(), modification)
        self._saved = False
        try:
            self._savedName = os.path.split(self._settings['spectralData'])[-1][:-4]
        except:
            self._savedName = ''
        try:
            if self.search() == 0:
                self.setUpUi()
        except InvalidInputException as e:
            traceback.print_exc()
            QtWidgets.QMessageBox.warning(None, "Problem occured", e.__str__(), QtWidgets.QMessageBox.Ok)

    def search(self):
        '''
        Search for ions in spectrum: Calculates theo. isotope patterns, searches for these in the spectrum (peak list),
        models intensities, fixes problems by overlapping ions (2 user inputs possible for deleting ions)
        '''
        print("\n********** Creating fragment library **********")
        self._libraryBuilder = IntactLibraryBuilder(self._sequence, self._settings['modifications'],
                                                              self._configs['maxIso'], self._configs['approxIso'])
        self._libraryBuilder.createLibrary()
        self._libraryBuilder.addNewIsotopePattern()


        """Importing spectral pattern"""
        #spectralFile = os.path.join(path, 'Spectral_data','top-down', self._settings['spectralData'])
        print("\n********** Importing spectral pattern from:", self._settings['spectralData'], "**********")
        try:
            self._spectrumHandler = IntactSpectrumHandler(self._settings, self._configs)
        except Exception as e:
            raise InvalidInputException('Problem in file ' + self._settings['spectralData'] + ':<br>', e.__str__())
        self._info.spectrumProcessed(self._spectrumHandler.getUpperBound(), self._spectrumHandler.getNoiseLevel())
        if self._settings['calibration']:
            allSettings = dict(self._settings)
            allSettings.update(self._configs)
            self._calibrator = Calibrator(self._libraryBuilder.getNeutralLibrary(),allSettings)
            if not self.calibrate():
                return 1

        """Finding fragments"""
        print("\n********** Search for ions **********")
        start = time.time()
        self._spectrumHandler.findIons(self._libraryBuilder.getNeutralLibrary())
        print("\ndone\nexecution time: ", round((time.time() - start) / 60, 3), "min\n")

        self._intensityModeller = IntensityModeller(self._configs, self._spectrumHandler.getNoiseLevel())
        start = time.time()
        print("\n********** Calculating relative abundances **********")
        self.processIons()
        print("\ndone\nexecution time: ", round((time.time() - start) / 60, 3), "min\n")

        """Handle ions with same monoisotopic peak and charge"""
        print("\n********** Handling overlaps **********")
        sameMonoisotopics = self._intensityModeller.findIsomers()
        print('mono', sameMonoisotopics)
        if len(sameMonoisotopics) > 0:
            view = CheckMonoisotopicOverlapView(sameMonoisotopics, self._spectrumHandler)
            print("User Input requested")
            view.exec_()
            if view and not view.canceled():
                dumpList = view.getDumplist()
                [self._info.deleteMonoisotopic(ion) for ion in dumpList]
                self._intensityModeller.deleteIsomers(dumpList)
            else:
                return 1

        """remodelling overlaps"""
        print("\n********** Re-modelling overlaps **********")
        complexPatterns = self._intensityModeller.remodelOverlaps()
        self._intensityModeller.remodelComplexPatterns(complexPatterns, [])
        self._info.searchFinished(self._spectrumHandler.getUpperBound())
        print("done")
        return 0


    def createMenuBar(self):
        '''
        Makes the QMenuBar
        :return:
        '''
        self._mainWindow.createMenuBar()
        self._actions = dict()
        _,actions = self._mainWindow.createMenu("File", {#'Save': (self.saveAnalysis, None, "Ctrl+S"),
                                'Export and Analysis': (self.export,'Analyses and exports the results to Excel',None),
                                'Close': (self.close,None,"Ctrl+Q")}, None)
        self._actions.update(actions)
        self._actions.update(self.makeGeneralOptions())


    def export(self):
        '''
        Exports the results to a xlsx file
        '''
        exportConfigHandler = ConfigurationHandlerFactory.getIntactExportHandler()
        dlg = ExportDialog(self._mainWindow, (), exportConfigHandler.getAll())
        dlg.exec_()
        if dlg and not dlg.canceled():
            newOptions = dlg.getOptions()
            exportConfigHandler.write(newOptions)
            filename = dlg.getFilename()
            if filename == '':
                inputFileName = os.path.split(self._settings['spectralData'])[-1]
                filename = inputFileName[0:-4] + '.xlsx'
            elif filename[-5:] != '.xlsx':
                filename += '.xlsx'
            outputPath = newOptions['dir']
            if outputPath == '':
                outputPath = os.path.join(path, 'Spectral_data', 'top-down')
            output = os.path.join(outputPath, filename)
            if os.path.isfile(output):
                choice = QtWidgets.QMessageBox.question(self._mainWindow, "Overwriting",
                                                        "There is already an file with the name: " + filename + "\nDo you want to overwrite it?",
                                                        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                if choice == QtWidgets.QMessageBox.No:
                    return
            parameters = {'data:': outputPath, 'date:': datetime.now().strftime("%d/%m/%Y %H:%M")}
            parameters.update(self._settings)
            parameters.update(self._configs)
            del parameters['spectralData']
            excelWriter = FullIntactExcelWriter(output, self._configs, newOptions)
            analyser = IntactAnalyser([[self._intensityModeller.getObservedIons().values()]], self._configs['useAb'])
            #avCharges, avErrors, stddevs = analyser.calculateAvChargeAndError()
            try:
                excelWriter.toExcel(analyser, self._intensityModeller, self._libraryBuilder.getNeutralLibrary(),
                                    self._settings, self._spectrumHandler, self._info.toString())
                self._info.export(output)
                print("********** saved in:", output, "**********\n")
                try:
                    autoStart(output)
                except:
                    pass
                print("saved in:", output)
            except:
                traceback.print_exc()
