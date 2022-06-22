'''
Created on 21 Jul 2020

@author: michael
'''

import traceback
import os

import numpy as np
import time
from PyQt5 import QtWidgets

from src.resources import path, autoStart
from src.Exceptions import InvalidIsotopePatternException, InvalidInputException
from src.entities.Info import Info
from src.gui.AbstractMainWindows import SimpleMainWindow
from src.gui.controller.AbstractController import AbstractMainController
from src.gui.tableviews.FragmentationTable import FragmentationTable
from src.gui.widgets.OccupancyWidget import OccupancyWidget
from src.gui.widgets.SequCovWidget import SequCovWidget
from src.repositories.ConfigurationHandler import ConfigurationHandlerFactory
from src.repositories.IsotopePatternRepository import IsotopePatternRepository
from src.services.analyser_services.Analyser import Analyser
from src.entities.SearchSettings import SearchSettings
from src.services.assign_services.Calibrator import Calibrator
from src.services.library_services.FragmentLibraryBuilder import FragmentLibraryBuilder
from src.services.SearchService import SearchService
from src.services.assign_services.TD_SpectrumHandler import SpectrumHandler
from src.services.IntensityModeller import IntensityModeller
from src.repositories.export.ExcelWriter import ExcelWriter
from src.gui.dialogs.CheckIonView import CheckMonoisotopicOverlapView, CheckOverlapsView
from src.gui.tableviews.PlotTables import PlotTableView
from src.gui.widgets.SequencePlots import PlotFactory, plotBars
from src.gui.dialogs.SimpleDialogs import ExportDialog, SelectSearchDlg, OpenSpectralDataDlg, SaveSearchDialog
#from src.gui.ParameterDialogs import TDStartDialog
from src.gui.dialogs.StartDialogs import TDStartDialog

"""def sortIonsByName(ionList):
    #return sorted(ionList,key=lambda obj:(obj.type ,obj.number))
    return sorted(ionList, key=lambda obj: (obj.getName(), obj.getCharge()))"""



#if __name__ == '__main__':
class TD_MainController(AbstractMainController):
    '''
    Controller class for starting, saving, exporting and loading a top-down search/analysis
    '''
    def __init__(self, parent, new, window):
        '''
        Starts either the search or loads a search from the database. Afterwards, result windows are shown.
        :param parent:
        :param (bool) new: True if new search, False if old search is loaded
        '''
        super(TD_MainController, self).__init__(window)
        if new:
            dialog = TDStartDialog(parent)
            dialog.exec_()
            if dialog.canceled():
                return
            self._settings = dialog.newSettings()
            self._configs = ConfigurationHandlerFactory.getConfigHandler().getAll()
            self._propStorage = SearchSettings(self._settings['sequName'], self._settings['fragmentation'],
                                               self._settings['modifications'])
            self._info = Info(self._settings, self._configs, self._propStorage)
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
        else:
            searchService = SearchService()
            #self._search =
            dialog = SelectSearchDlg(parent, searchService.getAllSearchNames(),self.deleteSearch, searchService)
            if dialog.exec_() and not dialog.canceled():
                self._configs = ConfigurationHandlerFactory.getConfigHandler().getAll()
                start=time.time()
                self._settings, noiseLevel, observedIons, delIons, remIons, searchedZStates, logFile = \
                    searchService.getSearch(dialog.getName())
                print('time:', time.time()-start)
                self._info = Info(logFile)
                self._savedName = dialog.getName()
                peaks = None
                if not os.path.isfile(self._settings['spectralData']):
                    choice = QtWidgets.QMessageBox.question(parent, 'Spectral Data not found!',
                        'File with spectral data could not be found.\n'
                        'Do you want to manually select the file? Otherwise, the analysis will be loaded without the '
                        'spectral data.',
                        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                    if choice == QtWidgets.QMessageBox.Yes:
                        dlg = OpenSpectralDataDlg(parent)
                        if dlg.exec_() and not dlg.canceled():
                            self._settings['spectralData'] = dlg.getValue()
                    elif choice == QtWidgets.QMessageBox.No:
                        peaks = searchService.getAllAssignedPeaks(observedIons+delIons)
                self._propStorage = SearchSettings(self._settings['sequName'], self._settings['fragmentation'],
                                                   self._settings['modifications'])
                self._libraryBuilder = FragmentLibraryBuilder(self._propStorage, self._settings['nrMod'],
                                                              self._configs['maxIso'], self._configs['approxIso'])
                self._libraryBuilder.createFragmentLibrary()

                self._spectrumHandler = SpectrumHandler(self._propStorage, self._libraryBuilder.getPrecursor(),
                                                        self._settings, self._configs, peaks)
                self._spectrumHandler.setSearchedChargeStates(searchedZStates)
                self._intensityModeller = IntensityModeller(self._configs, noiseLevel)
                self._intensityModeller.setIonLists(observedIons, delIons, remIons)
                self._analyser = Analyser(None, self._propStorage.getSequenceList(), self._settings['charge'],
                                          self._propStorage.getModificationName(), self._configs['useAb'])
                self._saved = True
                self.setUpUi()

    @staticmethod
    def deleteSearch(name, searchService):
        searchService.deleteSearch(name)


    def search(self):
        '''
        Search for ions in spectrum: Calculates theo. isotope patterns, searches for these in the spectrum (peak list),
        models intensities, fixes problems by overlapping ions (2 user inputs possible for deleting ions)
        '''
        print("\n********** Creating fragment library **********")
        self._libraryBuilder = FragmentLibraryBuilder(self._propStorage, self._settings['nrMod'],
                                                      self._configs['maxIso'], self._configs['approxIso'])
        self._libraryBuilder.createFragmentLibrary()

        """read existing ion-list file or create new one"""
        libraryImported = False
        patternReader = IsotopePatternRepository()
        if self._settings['fragLib'] != '':
            settings = [self._settings['fragLib']]
        else:
            settings = [self._settings[setting] for setting in ['sequName', 'fragmentation', 'nrMod', 'modifications']]
        if patternReader.findFile(settings):
            print("\n********** Importing list of isotope patterns from:", patternReader.getFile(), "**********")
            try:
                self._libraryBuilder.setFragmentLibrary(patternReader)
                libraryImported = True
                print("done")
            except InvalidIsotopePatternException:
                traceback.print_exc()
                choice = QtWidgets.QMessageBox.question(None, "Problem with importing list of isotope patterns",
                        "Imported Fragment Library from " + patternReader.getFile() + " incomplete\n"
                        "Should a new library be created?\nThe search will be stopped otherwise",
                                                        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                if choice != QtWidgets.QMessageBox.Yes:
                    return 1
                    #sys.exit()
        if libraryImported == False:
            print("\n********** Writing new list of isotope patterns to:", patternReader.getFile(), "**********\n")
            #ld = LoadingWidget(len(self._libraryBuilder.getFragmentLibrary()), True)
            start = time.time()
            patternReader.saveIsotopePattern(self._libraryBuilder.addNewIsotopePattern())#ld.progress))
            print("\ndone\nexecution time: ", round((time.time() - start) / 60, 2), "min\n")

        """Importing spectral pattern"""
        if self._settings['spectralData'] == '':
            return 1
        #spectralFile = os.path.join(path, 'Spectral_data','top-down', self._settings['spectralData'])
        print("\n********** Importing spectral pattern from:", self._settings['spectralData'], "**********")
        self._spectrumHandler = SpectrumHandler(self._propStorage, self._libraryBuilder.getPrecursor(), self._settings,
                                                self._configs)
        self._info.spectrumProcessed(self._spectrumHandler.getUpperBound(), self._spectrumHandler.getNoiseLevel())
        #try:
        if self._settings['calibration']:
            allSettings = dict(self._settings)
            allSettings.update(self._configs)
            self._calibrator = Calibrator(self._libraryBuilder.getFragmentLibrary(),allSettings,
                                          self._spectrumHandler.getChargeRange)
            '''allSettings = dict(self._settings)
            allSettings.update(self._configs)
            self._calibrator = Calibrator(self._libraryBuilder.getFragmentLibrary(),allSettings,
                                          self._spectrumHandler.getChargeRange)
            dlg = CalibrationView(self._mainWindow, self._calibrator)
            dlg.exec_()
            if dlg and not dlg.canceled():
                self._calibrator.calibratePeaks(self._spectrumHandler.getSpectrum())
                vals = self._calibrator.getCalibrationValues()
                self._info.calibrate(vals[0], vals[1], self._calibrator.getQuality(), self._calibrator.getUsedIons())'''
            if not self.calibrate():
                return 1
        #except KeyError:
        #    pass
        """Finding fragments"""
        print("\n********** Search for ions **********")
        start = time.time()
        self._spectrumHandler.findIons(self._libraryBuilder.getFragmentLibrary())
        print("\ndone\nexecution time: ", round((time.time() - start) / 60, 3), "min\n")

        self._intensityModeller = IntensityModeller(self._configs, self._spectrumHandler.getNoiseLevel())
        start = time.time()
        print("\n********** Calculating relative abundances **********")
        for ion in self._spectrumHandler.getFoundIons():
            self._intensityModeller.processIons(ion)
        for ion in self._spectrumHandler._ionsInNoise:
            self._intensityModeller.processNoiseIons(ion)
        self._spectrumHandler.emptyLists()
        print("\ndone\nexecution time: ", round((time.time() - start) / 60, 3), "min\n")

        """Handle ions with same monoisotopic peak and charge"""
        print("\n********** Handling overlaps **********")
        sameMonoisotopics = self._intensityModeller.findSameMonoisotopics()
        if len(sameMonoisotopics) > 0:
            view = CheckMonoisotopicOverlapView(sameMonoisotopics, self._spectrumHandler.getSpectrum())
            print("User Input requested")
            view.exec_()
            if view and not view.canceled():
                dumpList = view.getDumplist()
                [self._info.deleteMonoisotopic(ion) for ion in dumpList]
                self._intensityModeller.deleteSameMonoisotopics(dumpList)
            else:
                return 1

        """remodelling overlaps"""
        print("\n********** Re-modelling overlaps **********")
        complexPatterns = self._intensityModeller.remodelOverlaps()
        if len(complexPatterns) > 0:
            view = CheckOverlapsView(complexPatterns, self._spectrumHandler.getSpectrum())
            print("User Input requested")
            view.exec_()
            if view and not view.canceled():
                dumpList = view.getDumplist()
                [self._info.deleteIon(ion) for ion in dumpList]
                self._intensityModeller.remodelComplexPatterns(complexPatterns, dumpList)
            else:
                return 1

        self._analyser = Analyser(None, self._propStorage.getSequenceList(), self._settings['charge'],
                                  self._propStorage.getModificationName(), self._configs['useAb'])
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
        _,actions = self._mainWindow.createMenu("File", {'Save': (self.saveAnalysis, None, "Ctrl+S"),
                                                         'Export': (self.export,'Exports the results to Excel',None),
                                                         'Close': (self.close,None,"Ctrl+Q")}, None)
        self._actions.update(actions)
        self._actions.update(self.makeGeneralOptions())
        _,actions = self._mainWindow.createMenu("Analysis",
                {'Fragmentation': (self.showFragmentation, 'Show fragmentation efficiencies (% of each fragment type)', None),
                 'Occupancies': (self.showOccupancyPlot,'Show occupancies as a function of sequence pos.',None),
                 'Charge States (int.)': (lambda: self.showChargeDistrPlot(False),'Show av. charge as a function of cleavage site (Calculated with int. values)',None),
                 'Charge States (int./z)':(lambda: self.showChargeDistrPlot(True),'Show av. charge as a function of cleavage site (Calculated with int./z values)',None),
                 'Sequence Coverage': (self.showSequenceCoverage,'Show sequence coverage',None)}, None)

        self._actions.update(actions)


    def makeTable(self, parent, data,fun):
        '''
        Makes an ion table
        '''
        return super(TD_MainController, self).makeTable(parent, data,fun,
                    self._intensityModeller.getPrecRegion(self._settings['sequName'], abs(self._settings['charge'])))


    def export(self):
        '''
        Exports the results to a xlsx file
        '''
        exportConfigHandler = ConfigurationHandlerFactory.getExportHandler()
        lastOptions= exportConfigHandler.getAll()
        if len(self._propStorage.getModifPattern().getItems()) != 0:
            options = ('occupancies','charge states (int.)','charge states (int./z)')
        else:
            options = ('charge states (int.)','charge states (int./z)')
        dlg = ExportDialog(self._mainWindow, options, lastOptions) #'sequence coverage'), lastOptions)
        dlg.exec_()
        if dlg and not dlg.canceled():
            self._info.export()
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
            self._configs['interestingIons'] = self.getInterestingIons()
            excelWriter = ExcelWriter(output, self._configs, newOptions)
            self._analyser.setIons(self.getIonList())
            try:
                excelWriter.toExcel(self._analyser, self._intensityModeller, self._propStorage,
                                    self._libraryBuilder.getFragmentLibrary(), self._settings, self._spectrumHandler,
                                    self._info.toString())
                print("********** saved in:", output, "**********\n")
                try:
                    autoStart(output)
                except:
                    pass
            except KeyError as e:
                traceback.print_exc()
                print(e.__str__(), 'not found')
                dlg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Information, 'Inaccurate Fragment List',
                                            e.__str__() + ' not found\n' +
                                        'The fragmentation pattern or the modification pattern was altered. '
                                        'Please change the corresponding values to the original ones (see protocol) and '
                                        'reload the analysis.', QtWidgets.QMessageBox.Ok, self._mainWindow, )
                if dlg.exec_() and dlg == QtWidgets.QMessageBox.Ok:
                    return

    def showFragmentation(self):
        '''
        Makes a widget with a table with the proportion of each fragment type and a table with the relative abundances
        for every fragment type and cleavage site. The latter is plotted (bar plot).
        '''
        self._analyser.setIons(self.getIonList())
        fragmentation, fragPerSite = self._analyser.calculateRelAbundanceOfSpecies()
        forwardVals = self._propStorage.filterByDir(fragPerSite, 1)
        backwardVals = self._propStorage.filterByDir(fragPerSite, -1)
        table = self._analyser.toTable(forwardVals.values(), backwardVals.values())
        headers= list(fragPerSite.keys())
        fragmentationView = FragmentationTable([(type,val) for type,val in fragmentation.items()],
                                               table, headers)
        self._openWindows.append(fragmentationView)
        plotBars(self._propStorage.getSequenceList(), np.array(table)[:,2:-2].astype(float), headers, '')


    def showOccupancyPlot(self):
        '''
        Makes a widget with 2 tables showing the relative occupancies and the absolute ones and plots both data sets
        '''
        #dlg = QtWidgets.QInputDialog()
        interestingIons = self.getInterestingIons()
        if interestingIons is None:
            return
        modification,ok = QtWidgets.QInputDialog.getText(self._mainWindow,'Show Occupancies', 'Enter the modification: ',
                                                         text=self._propStorage.getModificationName())
        if ok and modification!='':
            if modification[0] not in ('+','-'):
                modification = '+'+modification
            self._analyser.setIons(self.getIonList())
            percentageDict, absDict = self._analyser.calculateOccupancies(interestingIons, modification,
                                                                 self._propStorage.getUnimportantModifs())
            plotFactory = PlotFactory(self._mainWindow)
            forwardVals = self._propStorage.filterByDir(percentageDict,1)
            backwardVals = self._propStorage.filterByDir(percentageDict,-1)
            sequence = self._propStorage.getSequenceList()
            maxY=self._settings['nrMod']
            if modification!=self._propStorage.getModificationName():
                maxY=1
                if modification[1].isnumeric():
                    maxY=self._analyser.getNrOfModifications(modification, None)
            self._openWindows.append(plotFactory.showOccupancyPlot(sequence, forwardVals, backwardVals,maxY, modification))
            #absTable = np.zeros((len(sequence),len(absDict.keys())))
            forwardAbsVals = self._propStorage.filterByDir(absDict,1)
            backwardAbsVals = self._propStorage.filterByDir(absDict,-1)

            absTable = self._analyser.toTable(self.processAbsValues(list(forwardAbsVals.values())),
                                              self.processAbsValues(list(backwardAbsVals.values())))
            headers=[]
            for key in list(forwardAbsVals.keys())+list(backwardAbsVals.keys()):
                headers.append(key)
                headers.append(key+modification)
            '''occupView = PlotTableView(self._analyser.toTable(forwardVals.values(), backwardVals.values()),
                                           list(percentageDict.keys()), 'Occupancies: '+modification, 3,
                                      self._analyser.getPrecursorModification())'''
            occupView = OccupancyWidget(modification, self._analyser.toTable(forwardVals.values(), backwardVals.values()),
                                        list(percentageDict.keys()), self._analyser.getPrecursorModification(),
                                        absTable, headers)
            self._openWindows.append(occupView)
            plotBars(sequence, np.array(absTable)[:,2:-2].astype(float), headers, '', True)

    def getInterestingIons(self):
        interestingIons = ConfigurationHandlerFactory.getConfigHandler().get('interestingIons')
        if len(interestingIons) < 1:
            raise InvalidInputException('No interesting ions found',
                'Choose ions of interest within "Edit Parameters" menu to use this function')
        return interestingIons

    def processAbsValues(self, arrays):
        #rows, columns = len(arrays[0]), len(arrays)
        #finArray = np.zeros((rows, 2*columns))
        finArrays = []
        for arr in arrays:
            finArrays.append(arr[:,0])
            finArrays.append(arr[:,1])
        return finArrays


    def showChargeDistrPlot(self, reduced):
        '''
        Makes a widget with the charge plot and a table with the corresponding values
        :param (bool) reduced: True if the ion intensities should be divided by their charge
        '''
        self._analyser.setIons(self.getIonList())
        interestingIons = self.getInterestingIons()
        if interestingIons is None:
            return
        chargeDict, minMaxCharges = self._analyser.analyseCharges(interestingIons, reduced)
        if reduced:
            mainWindow, centralWidget, layout = self.getMainWindow('Charges State Analysis (I/z)')
        else:
            mainWindow, centralWidget, layout = self.getMainWindow('Charges State Analysis')
        plotFactory1 = PlotFactory(centralWidget)
        #plotFactory2 = PlotFactory(self._mainWindow)
        forwardVals = self._propStorage.filterByDir(chargeDict,1)
        backwardVals = self._propStorage.filterByDir(chargeDict,-1)
        forwardLimits = self._propStorage.filterByDir(minMaxCharges,1)
        backwardLimits = self._propStorage.filterByDir(minMaxCharges,-1)
        chargeView = PlotTableView(centralWidget, self._analyser.toTable(forwardVals.values(), backwardVals.values()),
                                       list(chargeDict.keys()), 'Av. Charge per Fragment', 1)
        chargeView.sortBy(1)
        layout.addWidget(chargeView)
        layout.addWidget(plotFactory1.showChargePlot(self._propStorage.getSequenceList(), forwardVals,
                                    backwardVals, self._spectrumHandler.getCharge(), forwardLimits, backwardLimits))
        mainWindow.show()
        #self._openWindows.append(chargeView)

    def getMainWindow(self, title):
        mainWindow = SimpleMainWindow(self._mainWindow, title)
        centralWidget = QtWidgets.QWidget(mainWindow)
        mainWindow.setCentralWidget(centralWidget)
        layout = QtWidgets.QHBoxLayout(centralWidget)
        self._openWindows.append(mainWindow)
        return mainWindow, centralWidget, layout


    def showSequenceCoverage(self):
        '''
        Calculates the sequence coverage details and makes a widget which shows the results
        '''
        global sequCovWidget
        self._analyser.setIons(self._intensityModeller.getObservedIons().values())
        coverages, calcCoverages, overall = self._analyser.getSequenceCoverage(self._propStorage.getFragmentsByDir(1))
        sequ = self._propStorage.getSequenceList()
        calcData =[(key,val*100) for key,val in calcCoverages.items()]
        #globalData = [list(val) for key,val in zip(('forward','backward'), np.transpose(overall[:,0:2]))]
        sequCovWidget = SequCovWidget(calcData, sequ, coverages[0], coverages[1], overall)
        self._openWindows.append(sequCovWidget)


    def saveAnalysis(self):
        '''
        Saves the results to the "search" - database
        '''
        searchService = SearchService()
        names = searchService.getAllSearchNames()
        while True:
            dlg = SaveSearchDialog(self._savedName)
            #name, ok = QtWidgets.QInputDialog.getText(self._mainWindow, 'Save Analysis', 'Enter the name: ')
            if dlg.exec_() and dlg.ok:
                self._savedName = dlg.getText()
                if self._savedName in names:
                    choice = QtWidgets.QMessageBox.question(self._mainWindow, "Overwriting",
                                "There is already a saved analysis with the name: " + self._savedName +"\nDo you want to overwrite it?",
                                                            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                    if choice == QtWidgets.QMessageBox.Yes:
                        break
                else:
                    break
            else:
                return
        print('Saving analysis', self._savedName)
        self._info.save()
        start=time.time()
        searchService.saveSearch(self._savedName, self._spectrumHandler.getNoiseLevel(), self._settings,
                                 self._intensityModeller.getObservedIons().values(),
                                 self._intensityModeller.getDeletedIons().values(),
                                 self._intensityModeller.getRemodelledIons(),
                                 self._spectrumHandler.getSearchedChargeStates(), self._info.toString())
        self._saved = True
        print('done')
        self._infoView.update()