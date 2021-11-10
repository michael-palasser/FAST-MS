'''
Created on 21 Jul 2020

@author: michael
'''
import subprocess
import traceback
import os
from datetime import datetime

import time
from PyQt5 import QtWidgets

from src import path
from src.Exceptions import InvalidInputException
from src.Services import IntactIonService, SequenceService
from src.entities.Info import Info
from src.entities.IonTemplates import IntactModification
from src.gui.controller.AbstractController import AbstractMainController
from src.intact.IntactAnalyser import IntactAnalyser
from src.intact.IntactExcelWriter import FullIntactExcelWriter
from src.intact.IntactFinder import Calibrator
from src.intact.IntactLibraryBuilder import IntactLibraryBuilder
from src.intact.IntactSpectrumHandler import IntactSpectrumHandler
from src.repositories.ConfigurationHandler import ConfigurationHandlerFactory
from src.top_down.IntensityModeller import IntensityModeller
from src.gui.dialogs.CheckIonView import CheckMonoisotopicOverlapView
from src.gui.dialogs.SimpleDialogs import ExportDialog
from src.gui.dialogs.StartDialogs import IntactStartDialogFull


FOTO_SESSION=True


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
        super(IntactMainController, self).__init__(parent, new, window)
        #self._mainWindow= window
        #if new:
        dialog = IntactStartDialogFull(None)
        dialog.exec_()
        if dialog.canceled():
            return
        self._settings = dialog.newSettings()
        self._configs = ConfigurationHandlerFactory.getTD_ConfigHandler().getAll()
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
        '''else:
            searchService = SearchService()
            #self._search =
            dialog = SelectSearchDlg(parent, searchService.getAllSearchNames(),self.deleteSearch, searchService)
            if dialog.exec_() and not dialog.canceled():
                self._configs = ConfigurationHandlerFactory.getTD_ConfigHandler().getAll()
                start=time.time()
                self._settings, observedIons, delIons, remIons, searchedZStates, logFile = \
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
                self._libraryBuilder = FragmentLibraryBuilder(self._propStorage, self._settings['nrMod'])
                self._libraryBuilder.createFragmentLibrary()

                self._spectrumHandler = SpectrumHandler(self._propStorage, self._libraryBuilder.getPrecursor(),
                                                        self._settings, peaks)
                self._spectrumHandler.setSearchedChargeStates(searchedZStates)
                self._intensityModeller = IntensityModeller(self._configs)
                self._intensityModeller.setIonLists(observedIons, delIons, remIons)
                self._analyser = Analyser(None, self._propStorage.getSequenceList(), self._settings['charge'],
                                          self._propStorage.getModificationName())
                self._saved = True
                self.setUpUi()'''

    '''@staticmethod
    def deleteSearch(name, searchService):
        searchService.deleteSearch(name)'''


    def search(self):
        '''
        Search for ions in spectrum: Calculates theo. isotope patterns, searches for these in the spectrum (peak list),
        models intensities, fixes problems by overlapping ions (2 user inputs possible for deleting ions)
        '''
        print("\n********** Creating fragment library **********")
        self._libraryBuilder = IntactLibraryBuilder(self._sequence, self._settings['modifications'])
        self._libraryBuilder.createLibrary()

        """read existing ion-list file or create new one"""
        """libraryImported = False
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
        print("\ndone\nexecution time: ", round((time.time() - start) / 60, 2), "min\n")"""
        self._libraryBuilder.addNewIsotopePattern()


        """Importing spectral pattern"""
        '''if self._settings['spectralData'] == '':
            return 1'''
        #spectralFile = os.path.join(path, 'Spectral_data','top-down', self._settings['spectralData'])
        print("\n********** Importing spectral pattern from:", self._settings['spectralData'], "**********")
        self._spectrumHandler = IntactSpectrumHandler(self._settings)
        if self._settings['calibration']:
            allSettings = dict(self._settings)
            allSettings.update(self._configs)
            self._calibrator = Calibrator(self._libraryBuilder.getNeutralLibrary(),allSettings)
            self._calibrator.calibratePeaks(self._spectrumHandler.getSpectrum())
            vals = self._calibrator.getCalibrationValues()
            self._info.calibrate(vals[0], vals[1], self._calibrator.getQuality(), self._calibrator.getUsedIons())
        """Finding fragments"""
        print("\n********** Search for ions **********")
        start = time.time()
        self._spectrumHandler.findIons(self._libraryBuilder.getNeutralLibrary())
        print("\ndone\nexecution time: ", round((time.time() - start) / 60, 3), "min\n")

        self._intensityModeller = IntensityModeller(self._configs)
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
        print('mono', sameMonoisotopics)
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
        '''if len(complexPatterns) > 0:
            view = CheckOverlapsView(complexPatterns, self._spectrumHandler.getSpectrum())
            print("User Input requested")
            view.exec_()
            if view and not view.canceled():
                dumpList = view.getDumplist()
                [self._info.deleteIon(ion) for ion in dumpList]'''
        self._intensityModeller.remodelComplexPatterns(complexPatterns, [])
        '''else:
            return 1'''
        '''self._analyser = IntactAnalyser(None, self._propStorage.getSequenceList(),
                                  self._settings['charge'], self._propStorage.getModificationName())'''
        self._info.searchFinished(self._spectrumHandler.getUpperBound())
        print("done")
        return 0

    """def setUpUi(self):
        '''
        Opens a SimpleMainWindow with the ion lists and a InfoView with the protocol
        '''
        self._openWindows = []
        #self._mainWindow = SimpleMainWindow(None, 'Results:  ' + os.path.split(self._settings['spectralData'])[-1])
        self._translate = QtCore.QCoreApplication.translate
        self._mainWindow.setWindowTitle(self._translate(self._mainWindow.objectName(),
                                                        'Results:  ' + os.path.split(self._settings['spectralData'])[-1]))
        self._openWindows.append(self._mainWindow)
        self._centralwidget = self._mainWindow.centralWidget()
        self.verticalLayout = QtWidgets.QVBoxLayout(self._centralwidget)
        self._tabWidget = QtWidgets.QTabWidget(self._centralwidget)
        self._infoView = InfoView(None, self._info)
        self._openWindows.append(self._infoView)
        self.createMenuBar()
        self.fillMainWindow()
        '''self._tables = []
        for data, name in zip((self._intensityModeller.getObservedIons(), self._intensityModeller.getDeletedIons()),
                               ('Observed Ions', 'Deleted Ions')):
            self.makeTabWidget(data, name)
        self.verticalLayout.addWidget(self._tabWidget)'''
        self._mainWindow.resize(1000, 900)
        self._mainWindow.show()"""


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
        _,actions = self._mainWindow.createMenu("Edit", {'Repeat ovl. modelling':
                            (self.repeatModellingOverlaps,'Repeat overlap modelling involving user inputs',None),
                                                         #'Add new ion':(self.addNewIonView, 'Add an ion manually', None),
                                                         'Take Shot':(self.shootPic,'', None),
                                                         }, None)
        self._actions.update(actions)
        _,actions = self._mainWindow.createMenu("Show",
                {'Results': (self._mainWindow.show, 'Show lists of observed and deleted ions', None),
                 'Original Values':(self.showRemodelledIons,'Show original values of overlapping ions',None),
                 'Protocol':(self._infoView.show,'Show Protocol',None)}, None)
        '''_,actions = self._mainWindow.createMenu("Analysis",
                {'Fragmentation': (self.showFragmentation, 'Show fragmentation efficiencies (% of each fragment type)', None),
                 'Occupancy-Plot': (self.showOccupancyPlot,'Show occupancies as a function of sequence pos.',None),
                 'Charge-Plot': (lambda: self.showChargeDistrPlot(False),'Show av. charge as a function of sequence pos. (Calculated with Int. values)',None),
                 'Reduced Charge-Plot':(lambda: self.showChargeDistrPlot(True),'Show av. charge as a function of sequence pos. (Calculated with Int./z values)',None),
                 'Sequence Coverage': (self.showSequenceCoverage,'Show sequence coverage',None)}, None)

        self._actions.update(actions)'''
        '''if self._settings['modifications'] == '-':
            self._actions['Occupancy-Plot'].setDisabled(True)'''
        '''if len(self._configs['interestingIons'])<1:
            for action in ['Occupancy-Plot','Charge-Plot','Reduced Charge-Plot']:
                self._actions[action].setDisabled(True)
                self._actions[action].setToolTip('Choose ions of interest within "Edit Parameters" menu to use this function')
'''


    """def fillMainWindow(self):
        '''
        Makes a QTabWidget with the ion tables
        :return:
        '''
        self._tables = []
        for table, name in zip((self._intensityModeller.getObservedIons(), self._intensityModeller.getDeletedIons()),
                               ('Observed Ions', 'Deleted Ions')):
            self.makeTabWidget(table, name)
        self.verticalLayout.addWidget(self._tabWidget)

    def makeTabWidget(self, data, name):
        '''
        Makes a tab in the tabwidget
        :param data:
        :param name:
        :return:
        '''
        #if len(data)>0:
        tab = QtWidgets.QWidget()
        verticalLayout = QtWidgets.QVBoxLayout(tab)
        #tab.setLayout(_verticalLayout)
        self._tabWidget.addTab(tab, "")
        self._tabWidget.setTabText(self._tabWidget.indexOf(tab), self._translate(self._mainWindow.objectName(), name))
        scrollArea,table = self.makeScrollArea(tab,[ion.getMoreValues() for ion in data.values()], self.showOptions)
        verticalLayout.addWidget(scrollArea)
        self._tables.append(table)
        self._tabWidget.setEnabled(True)
        #self._tabWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        #tab.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        # _scrollArea.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

    def makeScrollArea(self, parent, data, fun):
        '''
        Makes QScrollArea for ion tables
        '''
        scrollArea = QtWidgets.QScrollArea(parent)
        #_scrollArea.setGeometry(QtCore.QRect(10, 10, 1150, 800))
        scrollArea.setWidgetResizable(True)
        # _scrollArea.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        # _scrollArea.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        table = self.makeTable(scrollArea, data, fun)
        table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        table.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        scrollArea.setWidget(table)
        return scrollArea, table

    def makeTable(self, parent, data,fun):
        '''
        Makes an ion table
        '''
        tableModel = IonTableModel(data, None, self._configs['shapeMarked'], self._configs['scoreMarked'])
        table = QtWidgets.QTableView(parent)
        table.setModel(tableModel)
        table.setSortingEnabled(True)
        #table.setModel(self.proxyModel)
        '''table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        table.customContextMenuRequested['QPoint'].connect(partial(fun, table))'''
        connectTable(table, fun)
        #table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        table.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        return table



    def showOptions(self, table, pos):
        '''
        Right-click options of an ion table
        '''
        menu = QtWidgets.QMenu()
        showAction = menu.addAction("Show in Spectrum")
        peakAction = menu.addAction("Show Peaks")
        formulaAction = menu.addAction("Get Formula")
        copyRowAction = menu.addAction("Copy Row")
        copyTableAction = menu.addAction("Copy Table")
        actionStrings = ["Delete", "Restore"]
        mode = 0
        other = 1
        if table != self._tables[0]:
            mode = 1
            other = 0
        delAction = menu.addAction(actionStrings[mode])
        action = menu.exec_(table.viewport().mapToGlobal(pos))
        it = table.indexAt(pos)
        if it is None:
            return
        selectedRow = it.row()
        selectedHash = table.model().getHashOfRow(selectedRow)
        selectedIon = self._intensityModeller.getIon(selectedHash)
        if action == showAction:
            global spectrumView
            ajacentIons, minLimit, maxLimit  = self._intensityModeller.getAdjacentIons(selectedHash)
            #minWindow, maxWindow, maxY = self._intensityModeller.getLimits(ajacentIons)
            peaks = self._spectrumHandler.getSpectrum(minLimit - 1, maxLimit + 1)
            spectrumView = SpectrumView(None, peaks, ajacentIons, np.min(selectedIon.getIsotopePattern()['m/z']),
                                np.max(selectedIon.getIsotopePattern()['m/z']),
                                        np.max(selectedIon.getIsotopePattern()['relAb']))
            self._openWindows.append(spectrumView)
        elif action == peakAction:
            #global peakview
            peakView = PeakView(self._mainWindow, selectedIon, self._intensityModeller.remodelSingleIon, self.saveSingleIon)
            self._openWindows.append(peakView)
        elif action == formulaAction:
            text = 'Ion:\t' + selectedIon.getName()+\
                   '\n\nFormula:\t'+selectedIon.getFormula().toString()
            QtWidgets.QMessageBox.information(self._mainWindow, selectedIon.getName(), text, QtWidgets.QMessageBox.Ok)
        elif action == copyRowAction:
            df=pd.DataFrame(data=[table.model().getRow(selectedRow)], columns=table.model().getHeaders())
            df.to_clipboard(index=False,header=True)
        elif action == copyTableAction:
            df=pd.DataFrame(data=table.model().getData(), columns=table.model().getHeaders())
            df.to_clipboard(index=False,header=True)
        elif action == delAction:
            choice = QtWidgets.QMessageBox.question(self._mainWindow, "",
                                        actionStrings[mode][:-1] +'ing ' + selectedIon.getName() +"?",
                                                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if choice == QtWidgets.QMessageBox.Yes:
                if mode ==0:
                    self._info.deleteIon(selectedIon)
                else:
                    self._info.restoreIon(selectedIon)
                self._saved = False
                ovHash = self._intensityModeller.switchIon(selectedIon)
                table.model().removeData(selectedRow)
                self._tables[other].model().addData(selectedIon.getMoreValues())
                print(actionStrings[mode]+"d",selectedRow, selectedHash)
                if ovHash is not None:
                    choice = QtWidgets.QMessageBox.question(self._mainWindow, "Attention",
                                                            'Deleted Ion overlapped with '+ovHash[0]+', '+str(ovHash[1])+'\n'+
                                                            'Should this ion be updated?',
                                                            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                    if choice == QtWidgets.QMessageBox.Yes:
                        ion = self._intensityModeller.resetIon(ovHash)
                        self._info.resetIon(ion)
                        self._tables[mode].model().updateData(ion.getMoreValues())
                self._infoView.update()


    def saveSingleIon(self, newIon):
        '''
        To save an ion which was changed in PeakView
        '''
        newIonHash = newIon.getHash()
        if newIonHash in self._intensityModeller.getObservedIons():
            ionDict = self._intensityModeller.getObservedIons()
            index = 0
        else:
            ionDict = self._intensityModeller.getDeletedIons()
            index = 1
        oldIon = ionDict[newIonHash]
        if newIon.getIntensity() == 0:
            dlg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Information, 'Invalid Request',
                                        'New intensity must not be 0', QtWidgets.QMessageBox.Ok, self._mainWindow)
            dlg.show()
        elif oldIon.getIntensity() != newIon.getIntensity():
            choice = QtWidgets.QMessageBox.question(self._mainWindow, 'Saving Ion',
                                                    "Please confirm to change the values of ion: " + oldIon.getId(),
                                                    QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
            if choice == QtWidgets.QMessageBox.Ok:
                self._info.changeIon(oldIon, newIon)
                self._infoView.update()
                self._saved = False
                #self._intensityModeller.addRemodelledIon(oldIon)
                #newIon.addComment('man.mod.')
                #ionDict[newIonHash] = newIon
                self._tables[index].model().updateData(self._intensityModeller.addRemodelledIon(newIon, index).getMoreValues())
                print('Saved', newIon.getId())


    def addNewIonView(self):
        '''
        Starts an AddIonView to create a new ion (which was not found by the main search)
        '''
        addIonView = AddIonView(self._mainWindow, self._propStorage.getMolecule().getName(),
                                ''.join(self._propStorage.getSequenceList()), self._settings['fragmentation'],
                                self._settings['modifications'], self.addNewIon)
        self._openWindows.append(addIonView)

    def addNewIon(self, addIonView):
        '''
        Adds a new ion to the table
        '''
        newIon = addIonView.getIon()
        newIon.setCharge(abs(newIon.getCharge()))
        self._intensityModeller.addNewIon(newIon)
        self._info.addNewIon(newIon)
        self._infoView.update()
        self._saved = False
        self._tables[0].model().addData(newIon.getMoreValues())
        addIonView.close()

    def repeatModellingOverlaps(self):
        '''
        To repeat modelling overlaps after manually deleting some ions
        '''
        self._info.repeatModelling()
        self._saved = False
        self._intensityModeller.remodelOverlaps(True)
        self.verticalLayout.removeWidget(self._tabWidget)
        self._tabWidget.hide()
        del self._tabWidget
        self._tabWidget = QtWidgets.QTabWidget(self._centralwidget)
        self.fillMainWindow()"""

    '''def dumb(self):
        print('not yet implemented')
        dlg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Information, 'Unvalid Request',
                    'Sorry, not implemented yet', QtWidgets.QMessageBox.Ok, self._mainWindow, )
        if dlg.exec_() and dlg == QtWidgets.QMessageBox.Ok:
            return'''

    def export(self):
        '''
        Exports the results to a xlsx file
        '''
        exportConfigHandler = ConfigurationHandlerFactory.getIntactExportHandler()
        dlg = ExportDialog(self._mainWindow, (), exportConfigHandler.getAll())
        dlg.exec_()
        if dlg and not dlg.canceled():
            self._info.export()
            newOptions = dlg.getOptions()
            exportConfigHandler.write(newOptions)
            outputPath, filename = dlg.getDir(), dlg.getFilename()
            if filename == '':
                inputFileName = os.path.split(self._settings['spectralData'])[-1]
                filename = inputFileName[0:-4] + '_out' + '.xlsx'
            elif filename[-5:] != '.xlsx':
                filename += '.xlsx'
            if outputPath == '':
                outputPath = os.path.join(path, 'Spectral_data', 'top-down')
            output = os.path.join(outputPath, filename)
            parameters = {'data:': outputPath, 'date:': datetime.now().strftime("%d/%m/%Y %H:%M")}
            parameters.update(self._settings)
            parameters.update(self._configs)
            del parameters['spectralData']
            excelWriter = FullIntactExcelWriter(output, self._configs, newOptions)
            analyser = IntactAnalyser([[self._intensityModeller.getObservedIons().values()]])
            #avCharges, avErrors, stddevs = analyser.calculateAvChargeAndError()
            try:
                excelWriter.toExcel(analyser, self._intensityModeller, self._libraryBuilder.getNeutralLibrary(),
                                    self._settings, self._spectrumHandler, self._info.toString())
                print("********** saved in:", output, "**********\n")
                try:
                    subprocess.call(['open', output])
                except:
                    pass
                print("saved in:", output)
            except:
                traceback.print_exc()


    """def close(self):
        '''
        Closes the search
        '''
        message = ''
        if self._saved == False:
            message = 'Warning: Unsaved Results\n'
        choice = QtWidgets.QMessageBox.question(self._mainWindow, 'Close Search',
                                                message + "Do you really want to close the analysis?",
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if choice == QtWidgets.QMessageBox.Yes:
            [w.close() for w in self._openWindows]
            self._mainWindow.close()
            self._infoView.close()

    def showRemodelledIons(self):
        '''
        Makes a table with the original values of the remodelled ions
        '''
        remView = QtWidgets.QWidget()
        #title = 'Original Values of Overlapping Ions'
        remView._translate = QtCore.QCoreApplication.translate
        remView.setWindowTitle(self._translate(remView.objectName(), 'Original Values of Overlapping Ions'))
        ions = self._intensityModeller.getRemodelledIons()
        verticalLayout = QtWidgets.QVBoxLayout(remView)
        scrollArea, table = self.makeScrollArea(remView, [ion.getMoreValues() for ion in ions], self.showRedOptions)
        #table.customContextMenuRequested['QPoint'].connect(partial(self.showRedOptions, table))
        connectTable(table, self.showRedOptions)
        verticalLayout.addWidget(scrollArea)
        remView.resize(1000, 750)
        self._openWindows.append(remView)
        remView.show()

    def showRedOptions(self, table, pos):
        '''
        Right-click options of an ion table which shows the original values of the remodelled ions
        '''
        menu = QtWidgets.QMenu()
        showAction = menu.addAction("Show in Spectrum")
        peakAction = menu.addAction("Show Peaks")
        formulaAction = menu.addAction("Get Formula")
        copyRowAction = menu.addAction("Copy Row")
        copyTableAction = menu.addAction("Copy Table")
        action = menu.exec_(table.viewport().mapToGlobal(pos))
        it = table.indexAt(pos)
        if it is None:
            return
        selectedRow = it.row()
        selectedHash = table.model().getHashOfRow(selectedRow)
        selectedIon = self._intensityModeller.getRemodelledIon(selectedHash)
        if action == showAction:
            global view
            ajacentIons, minLimit, maxLimit  = self._intensityModeller.getAdjacentIons(selectedHash)
            ajacentIons = [ion for ion in ajacentIons if ion.getHash()!=selectedHash]
            peaks = self._spectrumHandler.getSpectrum(minLimit - 1, maxLimit + 1)
            view = SpectrumView(None, peaks, [selectedIon]+ajacentIons, np.min(selectedIon.getIsotopePattern()['m/z']),
                                np.max(selectedIon.getIsotopePattern()['m/z']), np.max(selectedIon.getIsotopePattern()['relAb']))
            self._openWindows.append(view)
        elif action == peakAction:
            global peakview
            peakview = SimplePeakView(None, selectedIon)
            self._openWindows.append(peakview)
        elif action == formulaAction:
            text = 'Ion:\t' + selectedIon.getName()+\
                   '\n\nFormula:\t'+selectedIon.getFormula().toString()
            QtWidgets.QMessageBox.information(self._mainWindow, selectedIon.getName(), text, QtWidgets.QMessageBox.Ok)
        elif action == copyRowAction:
            df=pd.DataFrame(data=[table.model().getRow(selectedRow)], columns=table.model().getHeaders())
            df.to_clipboard(index=False,header=True)
        elif action == copyTableAction:
            df=pd.DataFrame(data=table.model().getData(), columns=table.model().getHeaders())
            df.to_clipboard(index=False,header=True)"""

    '''def showLogFile(self):
        self._infoView.show()'''

    """def getIonList(self):
        return list(self._intensityModeller.getObservedIons().values())"""

    """def showFragmentation(self):
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
        plotBars(self._propStorage.getSequenceList(), np.array(table)[:,2:-2].astype(float), headers,
                 'Fragmentation Efficiencies')


    def showOccupancyPlot(self):
        '''
        Makes a widget with 2 tables showing the relative occupancies and the absolute ones and plots both data sets
        '''
        #dlg = QtWidgets.QInputDialog()
        modification,ok = QtWidgets.QInputDialog.getText(self._mainWindow,'Occupancy Plot', 'Enter the modification: ',
                                                         text=self._propStorage.getModificationName())
        if ok and modification!='':
            self._analyser.setIons(self.getIonList())
            percentageDict, absDict = self._analyser.calculateOccupancies(self._configs.get('interestingIons'), modification,
                                                                 self._propStorage.getUnimportantModifs())
            '''if percentageDict == None:
                dlg = QtWidgets.QMessageBox(self._mainWindow, title='Unvalid Request',
                            text='It is not possible to calculate occupancies for an unmodified molecule.',
                            icon=QtWidgets.QMessageBox.Information, buttons=QtWidgets.QMessageBox.Ok)
                if dlg == QtWidgets.QMessageBox.Ok:
                    return'''
            plotFactory = PlotFactory(self._mainWindow)
            forwardVals = self._propStorage.filterByDir(percentageDict,1)
            backwardVals = self._propStorage.filterByDir(percentageDict,-1)
            sequence = self._propStorage.getSequenceList()
            plotFactory.showOccupancyPlot(sequence, forwardVals, backwardVals,
                                          self._settings['nrMod'], modification)

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
                                      self._analyser.getModificationLoss())'''
            occupView = OccupancyWidget(modification, self._analyser.toTable(forwardVals.values(), backwardVals.values()),
                                        list(percentageDict.keys()), self._analyser.getModificationLoss(),
                                        absTable, headers)
            self._openWindows.append(occupView)
            plotBars(sequence, np.array(absTable)[:,2:-2].astype(float), headers, 'Abs. Occupancies: '+modification, True)

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
        chargeDict, minMaxCharges = self._analyser.analyseCharges(self._configs.get('interestingIons'), reduced)
        plotFactory1 = PlotFactory(self._mainWindow)
        #plotFactory2 = PlotFactory(self._mainWindow)
        forwardVals = self._propStorage.filterByDir(chargeDict,1)
        backwardVals = self._propStorage.filterByDir(chargeDict,-1)
        forwardLimits = self._propStorage.filterByDir(minMaxCharges,1)
        backwardLimits = self._propStorage.filterByDir(minMaxCharges,-1)
        plotFactory1.showChargePlot(self._propStorage.getSequenceList(), forwardVals, backwardVals,
                                    self._settings['charge'], forwardLimits, backwardLimits)
        chargeView = PlotTableView(self._analyser.toTable(forwardVals.values(), backwardVals.values()),
                                       list(chargeDict.keys()), 'Av. Charge per Fragment', 1)
        self._openWindows.append(chargeView)
        '''plotFactory2.showChargePlot(self._libraryBuilder.getSequenceList(),
                                      self._libraryBuilder.filterByDir(redChargeDict,1),
                                      self._libraryBuilder.filterByDir(redChargeDict,-1),self._settings['charge'])'''


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
                                "There is already a saved analysis with name: " + self._savedName +"\nDo you want to overwrite it?",
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
        searchService.saveSearch(self._savedName, self._settings, self._intensityModeller.getObservedIons().values(),
                                 self._intensityModeller.getDeletedIons().values(),
                                 self._intensityModeller.getRemodelledIons(),
                                 self._spectrumHandler.getSearchedChargeStates(), self._info.toString())
        self._saved = True
        print('time:',time.time()-start)
        print('done')
        self._infoView.update()"""