'''
Created on 21 Jul 2020

@author: michael
'''
import logging
import traceback
import os
import numpy as np
import time
from PyQt5 import QtWidgets

from src.entities.InternalIons import InternalFragmentIon
from src.resources import path, autoStart, DEVELOP, getRelativePath
from src.Exceptions import InvalidIsotopePatternException, InvalidInputException
from src.entities.Info import Info
from src.gui.mainWindows.AbstractMainWindows import SimpleMainWindow
from src.gui.controller.AbstractController import AbstractMainController
from src.gui.tableviews.FragmentationTable import FragmentationTable
from src.gui.widgets.OccupancyWidget import OccupancyWidget
from src.gui.widgets.SequCovWidget import SequCovWidget
from src.repositories.ConfigurationHandler import ConfigurationHandlerFactory
from src.repositories.IsotopePatternRepository import IsotopePatternRepository
from src.services.DataBaseConverter import DataBaseConverter
from src.services.StoredAnalysesService import StoredAnalysesService
from src.services.analyser_services.Analyser import Analyser
from src.entities.SearchSettings import SearchSettings
from src.services.assign_services.Calibrator import Calibrator
from src.services.library_services.FragmentLibraryBuilder import FragmentLibraryBuilder
from src.services.assign_services.TD_SpectrumHandler import SpectrumHandler
from src.services.IntensityModeller import IntensityModeller
from src.repositories.export.ExcelWriter import ExcelWriter
from src.gui.dialogs.CheckIonView import CheckMonoisotopicOverlapView, CheckOverlapsView
from src.gui.tableviews.PlotTables import PlotTableView
from src.gui.widgets.SequencePlots import PlotFactory, plotBars
from src.gui.dialogs.SimpleDialogs import ExportDialog, SelectSearchDlg, OpenSpectralDataDlg, SaveSearchDialog
from src.gui.dialogs.StartDialogs import TDStartDialog
from src.gui.GUI_functions import shoot

"""def sortIonsByName(ionList):
    #return sorted(ionList,key=lambda obj:(obj.type ,obj.number))
    return sorted(ionList, key=lambda obj: (obj.getName(), obj.getCharge()))"""



#if __name__ == '__main__':
class TD_MainController(AbstractMainController):
    '''
    Controller class for starting, saving, exporting and loading a top-down search/analysis
    '''
    def __init__(self, parent, new, window, special=None):
        '''
        Starts either the search or loads a search from the database. Afterwards, result windows are shown.
        :param parent:
        :param (bool) new: True if new search, False if old search is loaded
        '''
        super(TD_MainController, self).__init__(window)
        if new:
            dialog = self.startDialog(parent)
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
            try:
                self.loadSearch(parent,special)
            except IndexError as e:
                traceback.print_exc()
                logging.exception(e.__str__())
                QtWidgets.QMessageBox.warning(None, "Problem occured", e.__str__(), QtWidgets.QMessageBox.Ok)

            """searchService = SearchService()
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
                self.setUpUi()"""

    #new:
    @staticmethod
    def startDialog(parent):
        return TDStartDialog(parent)

    def loadSearch(self,parent, special):
        searchService = StoredAnalysesService()
        if special is None:
            self.checkOldDatabase()
            allNames, corrupt = searchService.getAllSearchNames(True)
            if len(corrupt)>0:
                """QtWidgets.QMessageBox.warning(None, "Corrupted Directories",
                                              "The following directories are corrupted and should be deleted: "
                                              +  ", ".join(corrupt), QtWidgets.QMessageBox.Ok)"""
                choice = QtWidgets.QMessageBox.question(None, "Corrupted Directories",
                                                        "The following directories are corrupted: "
                                              +  ", ".join(corrupt)+'<br>Should the directories be deleted?',
                                                        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                if choice == QtWidgets.QMessageBox.Yes:
                    for searchName in corrupt:
                        searchService.deleteSearch(searchName)
            dialog = SelectSearchDlg(parent, allNames,self.deleteSearch, searchService)
            if dialog.exec_() and not dialog.canceled():
                self.load(dialog.getName(), searchService)
        else:
            self.load(special, searchService)


    def load(self, analysisName, searchService):
        start=time.time()
        self._settings, self._configs, noiseLevel, observedIons, delIons, searchedZStates, logs = \
            searchService.getSearch(analysisName)
        print('time:', time.time()-start)

        self._info = Info(logs)
        self._savedName = analysisName
        peaks = None
        if 'profile' not in self._settings.keys() or self._settings['profile']=="":
            keys = ('spectralData',)
        else:
            keys = ('spectralData', 'profile')
        for key in keys:
            if not os.path.isfile(self._settings[key]):
                choice = QtWidgets.QMessageBox.question(None, 'Spectral Data not found!',
                    'File with spectral data (' +self._settings[key]+ ') could not be found.<br>'
                    'Do you want to manually select the file? Otherwise, the analysis will be loaded without the '
                    'spectral data.',
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                if choice == QtWidgets.QMessageBox.Yes:
                    dlg = OpenSpectralDataDlg(None)
                    if dlg.exec_() and not dlg.canceled():
                        self._settings[key] = dlg.getValue()
                elif choice == QtWidgets.QMessageBox.No:
                    peaks = searchService.getAllAssignedPeaks(observedIons+delIons)
        self._propStorage = SearchSettings(self._settings['sequName'], self._settings['fragmentation'],
                                            self._settings['modifications'])
        self._libraryBuilder = self.constructLibraryBuilder()
        self._libraryBuilder.createFragmentLibrary()
        noise = []
        for ion in observedIons+delIons:
            mostAb = np.sort(ion.getIsotopePattern(),order='I')[::-1][0]['m/z']
            noise.append((mostAb, ion.getNoise()))
        constructor = self.getSpectrumHandlerConstructor()
        self._spectrumHandler = constructor(self._propStorage, self._libraryBuilder.getPrecursor(),self._settings,
                                            self._configs, peaks, noise)
        self._spectrumHandler.setSearchedChargeStates(searchedZStates)
        self._intensityModeller = IntensityModeller(self._configs, noiseLevel)
        self._intensityModeller.setIonLists(observedIons, delIons, [])
        self._intensityModeller.setMonoisotopicList()

        types = self._propStorage.getFragmentsByDir(1)
        types.update(self._propStorage.getFragmentsByDir(-1))
        types.add(self._settings['sequName'])
        for key in {ion.getType() for ion in self._intensityModeller.getObservedIons().values()}:
            if (key not in types) and not isinstance(ion, InternalFragmentIon):
                QtWidgets.QMessageBox.warning(None, "Fragment type not found", '"'+ key + '" was not found in fragmentation template list. Add the template to "'
                                              + self._propStorage.getFragmentation().getName() + '" to ensure correct behaviour', QtWidgets.QMessageBox.Ok)
        self._analyser = Analyser(None, self._propStorage.getSequenceList(), self._settings['charge'],
                                    self._propStorage.getModificationName(), self._configs['useAb'])
        self._saved = True
        self.setUpUi()


    def checkOldDatabase(self):
        #print("os.path.isfile(getRelativePath(",os.path.isfile(getRelativePath("search.db")),getRelativePath("search.db"))
        if os.path.isfile(getRelativePath("search.db")):
            choice = QtWidgets.QMessageBox.question(None, "Convert Database","A database containing stored analyses in a deprecated format was found.<br>"
                                                    +"Should the data be converted? Depending on the number of stored analyses, this step can take some time.",
                                                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if choice == QtWidgets.QMessageBox.Yes:
                DataBaseConverter()

    def constructLibraryBuilder(self):
        return FragmentLibraryBuilder(self._propStorage, self._settings['nrMod'], self._configs['maxIso'],
                                      self._configs['approxIso'])

    @staticmethod
    def deleteSearch(name, searchService):
        searchService.deleteSearch(name)


    def search(self):
        '''
        Search for ions in spectrum: Calculates theo. isotope patterns, searches for these in the spectrum (peak list),
        models intensities, fixes problems by overlapping ions (2 user inputs possible for deleting ions)
        '''
        print("\n********** Creating fragment library **********")
        logging.info("********** Creating fragment library **********")
        start = time.time()
        self._libraryBuilder = self.constructLibraryBuilder()
        self._libraryBuilder.createFragmentLibrary()
        print("done", time.time()-start)
        """read existing ion-list file or create new one"""
        libraryImported = False
        patternReader = IsotopePatternRepository()
        settings = [self._settings[setting] for setting in ['sequName', 'fragmentation', 'nrMod', 'modifications']]
        if self._settings['fragLib'] != '':
            settings = [self._settings['fragLib']]
        if patternReader.findFile(settings):
            print("\n********** Importing list of isotope patterns from:", patternReader.getFile(), "**********")
            logging.info("********** Importing list of isotope patterns from: " + patternReader.getFile() + " **********")
            try:
                self._libraryBuilder.setFragmentLibrary(patternReader)
                libraryImported = True
                print("done")
            except InvalidIsotopePatternException:
                traceback.print_exc()
                choice = QtWidgets.QMessageBox.question(None, "Problem with importing list of isotope patterns",
                        "Imported Fragment Library from " + patternReader.getFile() + " incomplete<br>"
                        "Should a new library be created?<br>The search will be stopped otherwise",
                                                        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                if choice != QtWidgets.QMessageBox.Yes:
                    return 1
                    #sys.exit()
        if libraryImported == False:
            print("\n********** Writing new list of isotope patterns to:", patternReader.getFile(), "**********\n")
            logging.info("********** Writing new list of isotope patterns to: " + patternReader.getFile() + " **********")
            #ld = LoadingWidget(len(self._libraryBuilder.getFragmentLibrary()), True)
            start = time.time()
            patternReader.saveIsotopePattern(self._libraryBuilder.addNewIsotopePattern())#ld.progress))
            print("\ndone\nexecution time: ", round((time.time() - start) / 60, 2), "min\n")

        """Importing spectral data"""
        if self._settings['spectralData'] == '':
            return 1
        #spectralFile = os.path.join(path, 'Spectral_data','top-down', self._settings['spectralData'])
        print("\n********** Importing peak data from:", self._settings['spectralData'], "**********")
        logging.info("********** Importing peak data from: "+ self._settings['spectralData']+" **********")
        try:
            constructor = self.getSpectrumHandlerConstructor()
            self._spectrumHandler = constructor(self._propStorage, self._libraryBuilder.getPrecursor(),self._settings,
                                                self._configs)
        except Exception as e:
            traceback.print_exc()
            logging.exception(e.__str__())
            raise InvalidInputException('Problem in file ' + self._settings['spectralData'] + ':<br>', traceback.format_exc())
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
        logging.info("********** Search for ions **********")
        start = time.time()
        self._spectrumHandler.findIons(self._libraryBuilder.getFragmentLibrary())
        print("\ndone\nexecution time: ", round((time.time() - start) / 60, 3), "min\n")

        self._intensityModeller = IntensityModeller(self._configs, self._spectrumHandler.getNoiseLevel())
        start = time.time()
        print("\n********** Calculating relative abundances **********")
        logging.info("********** Calculating relative abundances **********")
        self.processIons()
        print("\ndone\nexecution time: ", round((time.time() - start) / 60, 3), "min\n")

        """Handle ions with same monoisotopic peak and charge"""
        print("\n********** Handling overlaps **********")
        logging.info("********** Handling isomers **********")
        sameMonoisotopics = self._intensityModeller.findIsomers()
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
        logging.info("********** Re-modelling overlaps **********")
        complexPatterns = self._intensityModeller.remodelOverlaps()
        if len(complexPatterns) > 0:
            view = CheckOverlapsView(complexPatterns, self._spectrumHandler)
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

    def getSpectrumHandlerConstructor(self):
        return SpectrumHandler


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
                {'Fragmentation Yields': (self.showFragmentation, 'Determines the site-specific fragment yields', None),
                 'Localise Modifications': (self.showOccupancyPlot,'Relatively quantifies the site-specific labeled fractions. Works for covalent and non-covalent modifications',None),
                 'Charge States (int.)': (lambda: self.showChargeDistrPlot(False),'Show av. charge as a function of cleavage site (Calculated using int. values)',None),
                 'Charge States (int./z)':(lambda: self.showChargeDistrPlot(True),'Show av. charge as a function of cleavage site (Calculated using int./z values)',None),
                 'Sequence Coverage': (self.showSequenceCoverage,'Show sequence coverage',None)}, None)

        self._actions.update(actions)

    def getEditOptions(self):
        return {'Repeat Ovl. Modelling':
                   (self.repeatModellingOverlaps, 'Repeat overlap modelling involving user inputs', None),
                    'Add New Ion':(self.addNewIonView, 'Add an ion manually', None),}

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
        lastOptions['dir'] = os.path.dirname(self._settings['spectralData'])
        if len(self._propStorage.getModifPattern().getItems()) != 0:
            options = ('localise modification','charge states (int.)','charge states (int./z)')
        else:
            options = ('charge states (int.)','charge states (int./z)')
        dlg = ExportDialog(self._mainWindow, options, lastOptions) #'sequence coverage'), lastOptions)
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
                choice = QtWidgets.QMessageBox.question(self._mainWindow, "Warning",
                                                        "There is already an file with the name: " + filename + "<br>Do you want to overwrite it?",
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
                self._info.export(output)
                print("********** saved in:", output, "**********\n")
                logging.info("********** exported to: "+ output+ "**********")
                try:
                    autoStart(output)
                except Exception as e:
                    logging.exception(e.__str__())
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
            except Exception as e:
                if "Permission" in e.__str__():
                    QtWidgets.QMessageBox.warning(None, "File not closed", 'You have to close the file "'+
                                                  filename+'" to overwrite it', QtWidgets.QMessageBox.Ok)
                else:
                    raise e

    def showFragmentation(self):
        '''
        Makes a widget with a table with the proportion of each fragment type and a table with the relative abundances
        for every fragment type and cleavage site. The latter is plotted (bar plot).
        '''
        self._analyser.setIons(self.getIonList())
        if DEVELOP:
            for ion in self.getIonList():
                sortedArray = np.sort(ion.getIsotopePattern(), order='I')[::-1]
                print(ion.getName(), ion.getCharge(), ion.getType(), ion.getNumber(), ion.getModification(),
                      sortedArray['m/z'][0], sortedArray['calcInt'][0], ion.getSignalToNoise())
        fragmentation, fragPerSite = self._analyser.calculateRelAbundanceOfSpecies()
        forwardVals = self._propStorage.filterByDir(fragPerSite, 1)
        backwardVals = self._propStorage.filterByDir(fragPerSite, -1)
        if len(forwardVals.keys())+len(backwardVals.keys()) != (len(fragPerSite.keys())):
            forwardKeys, backwardKeys = forwardVals.keys(), backwardVals.keys()
            for key in fragPerSite.keys():
                if (key not in forwardKeys) and (key not in backwardKeys):
                    QtWidgets.QMessageBox.warning(None, "Fragment type not found", '"'+ key + '" was not found in fragmentation template list. Add the template "'+
                                                key+'" to "' + self._propStorage.getFragmentation().getName() + '" and try again', QtWidgets.QMessageBox.Ok)
                    return
                    """raise InvalidInputException("Fragment type not found", key + " was not found in fragmentation template list. Add the template "+
                                                key+" to " + self._propStorage.getFragmentation().getName() + " and try again")"""
        table = self._analyser.toTable(forwardVals.values(), backwardVals.values())
        headers= list(fragPerSite.keys())
        fragmentationView = FragmentationTable([(type,val) for type,val in fragmentation.items()],
                                               table, headers)
        if DEVELOP:
            shoot(fragmentationView)
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
        modification,ok = QtWidgets.QInputDialog.getText(self._mainWindow,'Localise Modifications', 'Enter the modification: ',
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
        plotFactory = PlotFactory(centralWidget)
        #plotFactory2 = PlotFactory(self._mainWindow)
        forwardVals = self._propStorage.filterByDir(chargeDict,1)
        backwardVals = self._propStorage.filterByDir(chargeDict,-1)
        forwardLimits = self._propStorage.filterByDir(minMaxCharges,1)
        backwardLimits = self._propStorage.filterByDir(minMaxCharges,-1)
        chargeView = PlotTableView(centralWidget, self._analyser.toTable(forwardVals.values(), backwardVals.values()),
                                       list(chargeDict.keys()), 'Av. Charge per Fragment', 1)
        chargeView.sortBy(1)
        layout.addWidget(chargeView,2)
        layout.addWidget(plotFactory.showChargePlot(self._propStorage.getSequenceList(), forwardVals,
                                    backwardVals, self._spectrumHandler.getCharge(), forwardLimits, backwardLimits),3)
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
        searchService = StoredAnalysesService()
        names = searchService.getAllSearchNames()[0]
        while True:
            dlg = SaveSearchDialog(self._savedName)
            #name, ok = QtWidgets.QInputDialog.getText(self._mainWindow, 'Save Analysis', 'Enter the name: ')
            if dlg.exec_() and dlg.ok:
                self._savedName = dlg.getText()
                if self._savedName in names:
                    choice = QtWidgets.QMessageBox.question(self._mainWindow, "Overwriting",
                                "There is already a saved analysis with the name: " + self._savedName +"<br>Do you want to overwrite it?",
                                                            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                    if choice == QtWidgets.QMessageBox.Yes:
                        break
                else:
                    break
            else:
                return
        print('Saving analysis', self._savedName)
        #start=time.time()
        searchService.saveSearch(self._savedName, self._spectrumHandler.getNoiseLevel(), self._settings, self._configs,
                                 self._intensityModeller.getObservedIons().values(),
                                 self._intensityModeller.getDeletedIons().values(),
                                 self._spectrumHandler.getSearchedChargeStates(), self._info.toString())
        self._info.save(self._savedName)
        self._saved = True
        print('done')
        logging.info('Analysis saved: ' + self._savedName)
        self._infoView.update()
        return self._savedName
