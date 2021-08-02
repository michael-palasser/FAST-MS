'''
Created on 21 Jul 2020

@author: michael
'''

import subprocess
import traceback
import os

import numpy as np
import time
import pandas as pd
from PyQt5 import QtWidgets, QtCore

from src import path
from src.Exceptions import InvalidIsotopePatternException, InvalidInputException
from src.entities.Info import Info
from src.gui.AbstractMainWindows import SimpleMainWindow
from src.gui.GUI_functions import connectTable
from src.gui.IsotopePatternView import AddIonView
from src.gui.tableviews.FragmentationTable import FragmentationTable
from src.gui.widgets.InfoView import InfoView
from src.repositories.ConfigurationHandler import ConfigurationHandlerFactory
from src.repositories.IsotopePatternRepository import IsotopePatternRepository
from src.top_down.Analyser import Analyser
from src.entities.SearchSettings import SearchSettings
from src.top_down.LibraryBuilder import FragmentLibraryBuilder
from src.top_down.SearchService import SearchService
from src.top_down.SpectrumHandler import SpectrumHandler
from src.top_down.IntensityModeller import IntensityModeller
from src.top_down.ExcelWriter import ExcelWriter
from src.gui.dialogs.CheckIonView import CheckMonoisotopicOverlapView, CheckOverlapsView
from src.gui.tableviews.TableModels import IonTableModel
from src.gui.tableviews.PlotTables import PlotTableView
from src.gui.tableviews.ShowPeaksViews import PeakView, SimplePeakView
from src.gui.widgets.SequencePlots import PlotFactory
from src.gui.dialogs.SimpleDialogs import ExportDialog, SelectSearchDlg, OpenSpectralDataDlg, SaveSearchDialog
#from src.gui.ParameterDialogs import TDStartDialog
from src.gui.dialogs.StartDialogs import TDStartDialog
from src.gui.widgets.SpectrumView import SpectrumView


def sortIonsByName(ionList):
    #return sorted(ionList,key=lambda obj:(obj.type ,obj.number))
    return sorted(ionList, key=lambda obj: (obj.getName(), obj.getCharge()))



#if __name__ == '__main__':
class TD_MainController(object):
    '''
    Controller class for starting, saving, exporting and loading a top-down search/analysis
    '''
    def __init__(self, parent, new):
        '''
        Starts either the search or loads a search from the database. Afterwards, result windows are shown.
        :param parent:
        :param (bool) new: True if new search, False if old search is loaded
        '''
        if new:
            dialog = TDStartDialog(None)
            dialog.exec_()
            if dialog.canceled():
                return
            self._settings = dialog.newSettings()
            self._configs = ConfigurationHandlerFactory.getTD_ConfigHandler().getAll()
            self._propStorage = SearchSettings(self._settings['sequName'], self._settings['fragmentation'],
                                               self._settings['modifications'])
            self._info = Info(self._settings, self._configs, self._propStorage)
            self._saved = False
            self._savedName = os.path.split(self._settings['spectralData'])[-1][:-4]
            try:
                if self.search() == 0:
                    self.setUpUi(parent)
            except InvalidInputException as e:
                traceback.print_exc()
                QtWidgets.QMessageBox.warning(None, "Problem occured", e.__str__(), QtWidgets.QMessageBox.Ok)
        else:
            searchService = SearchService()
            #self._search =
            dialog = SelectSearchDlg(parent, searchService.getAllSearchNames(),self.deleteSearch, searchService)
            if dialog.exec_() and not dialog.canceled():
                self._configs = ConfigurationHandlerFactory.getTD_ConfigHandler().getAll()
                self._settings, observedIons, delIons, remIons, searchedZStates, logFile = \
                    searchService.getSearch(dialog.getName())
                self._info = Info(logFile)
                self._savedName = dialog.getName()
                if not os.path.isfile(self._settings['spectralData']):
                    dlg = OpenSpectralDataDlg(parent)
                    if dlg.exec_() and not dlg.canceled():
                        self._settings['spectralData'] = dlg.getValue()
                self._propStorage = SearchSettings(self._settings['sequName'], self._settings['fragmentation'],
                                                   self._settings['modifications'])
                self._libraryBuilder = FragmentLibraryBuilder(self._propStorage, self._settings['nrMod'])
                self._libraryBuilder.createFragmentLibrary()

                self._spectrumHandler = SpectrumHandler(self._propStorage, self._libraryBuilder.getPrecursor(), self._settings)
                self._spectrumHandler.setSearchedChargeStates(searchedZStates)
                self._intensityModeller = IntensityModeller(self._configs)
                self._intensityModeller.setIonLists(observedIons, delIons, remIons)
                self._analyser = Analyser(None, self._propStorage.getSequenceList(), self._settings['charge'],
                                          self._propStorage.getModificationName())
                self._saved = True
                self.setUpUi(parent)

    @staticmethod
    def deleteSearch(name, searchService):
        searchService.deleteSearch(name)


    def search(self):
        '''
        Search for ions in spectrum: Calculates theo. isotope patterns, searches for these in the spectrum (peak list),
        models intensities, fixes problems by overlapping ions (2 user inputs possible for deleting ions)
        '''
        print("\n********** Creating fragment library **********")
        self._libraryBuilder = FragmentLibraryBuilder(self._propStorage, self._settings['nrMod'])
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
            start = time.time()
            patternReader.saveIsotopePattern(self._libraryBuilder.addNewIsotopePattern())
            print("\ndone\nexecution time: ", round((time.time() - start) / 60, 2), "min\n")

        """Importing spectral pattern"""
        if self._settings['spectralData'] == '':
            return 1
        #spectralFile = os.path.join(path, 'Spectral_data','top-down', self._settings['spectralData'])
        print("\n********** Importing spectral pattern from:", self._settings['spectralData'], "**********")
        self._spectrumHandler = SpectrumHandler(self._propStorage, self._libraryBuilder.getPrecursor(), self._settings)
        """Finding fragments"""
        print("\n********** Search for ions **********")
        start = time.time()
        self._spectrumHandler.findIons(self._libraryBuilder.getFragmentLibrary())
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
        self._analyser = Analyser(None, self._propStorage.getSequenceList(),
                                  self._settings['charge'], self._propStorage.getModificationName())
        self._info.searchFinished(self._spectrumHandler.getUpperBound())
        print("done")
        return 0

    def setUpUi(self, parent):
        '''
        Opens a SimpleMainWindow with the ion lists and a InfoView with the protocol
        '''
        self._openWindows = []
        self._mainWindow = SimpleMainWindow(parent, 'Results:  ' + os.path.split(self._settings['spectralData'])[-1])
        self._translate = QtCore.QCoreApplication.translate
        self._centralwidget = self._mainWindow.centralWidget()
        self.verticalLayout = QtWidgets.QVBoxLayout(self._centralwidget)
        self._tabWidget = QtWidgets.QTabWidget(self._centralwidget)
        self._infoView = InfoView(None, self._info)
        self.createMenuBar()
        self.fillMainWindow()
        '''self._tables = []
        for data, name in zip((self._intensityModeller.getObservedIons(), self._intensityModeller.getDeletedIons()),
                               ('Observed Ions', 'Deleted Ions')):
            self.makeTabWidget(data, name)
        self.verticalLayout.addWidget(self._tabWidget)'''
        self._mainWindow.resize(1000, 900)
        self._mainWindow.show()


    def createMenuBar(self):
        '''
        Makes the QMenuBar
        :return:
        '''
        self._mainWindow.createMenuBar()
        self._actions = dict()
        _,actions = self._mainWindow.createMenu("File", {'Save': (self.saveAnalysis, None, "Ctrl+S"),
                                'Export': (self.export,None,None), 'Close': (self.close,None,"Ctrl+Q")}, None)
        self._actions.update(actions)
        _,actions = self._mainWindow.createMenu("Edit", {'Repeat ovl. modelling':
                            (self.repeatModellingOverlaps,'Repeat overlap modelling involving user inputs',None),
                                                         'Add new ion':(self.addNewIonView, 'Add an ion manually', None)}, None)
        self._actions.update(actions)
        _,actions = self._mainWindow.createMenu("Show",
                {'Results': (self._mainWindow.show, 'Show lists of observed and deleted ions', None),
                 'Original Values':(self.showRemodelledIons,'Show original values of overlapping ions',None),
                 'Info File':(self._infoView.show,'Show Protocol',None)}, None)
        _,actions = self._mainWindow.createMenu("Analysis",
                {'Fragmentation': (self.showFragmentation, 'Show fragmentation efficiencies (% of each fragment type)', None),
                 'Occupancy-Plot': (self.showOccupancyPlot,'Show occupancies as a function of sequence pos.',None),
                 'Charge-Plot': (lambda: self.showChargeDistrPlot(False),'Show av. charge as a function of sequence pos. (Calculated with Int. values)',None),
                 'Reduced Charge-Plot':(lambda: self.showChargeDistrPlot(True),'Show av. charge as a function of sequence pos. (Calculated with Int./z values)',None),
                 'Sequence Coverage': (self.showSequenceCoverage,'Show sequence coverage',None)}, None)
        self._actions.update(actions)
        if self._settings['modifications'] == '-':
            self._actions['Occupancy-Plot'].setDisabled(True)
        if len(self._configs['interestingIons'])<1:
            for action in ['Occupancy-Plot','Charge-Plot','Reduced Charge-Plot']:
                self._actions[action].setDisabled(True)
                self._actions[action].setToolTip('Choose ions of interest within "Edit Parameters" menu to use this function')


    def fillMainWindow(self):
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
        tableModel = IonTableModel(data,
                                   self._intensityModeller.getPrecRegion(self._settings['sequName'], abs(self._settings['charge'])),
                                   self._configs['shapeMarked'], self._configs['scoreMarked'])
        """self.proxyModel = QSortFilterProxyModel()
        self.proxyModel.setSourceModel(model)"""
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
            self._openWindows.append(PeakView(self._mainWindow, selectedIon, self._intensityModeller.remodelSingleIon, self.saveSingleIon))
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
                                ''.join(self._propStorage.getSequenceList()), self.addNewIon)
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
        self.fillMainWindow()

    def dumb(self):
        print('not yet implemented')
        dlg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Information, 'Unvalid Request',
                    'Sorry, not implemented yet', QtWidgets.QMessageBox.Ok, self._mainWindow, )
        if dlg.exec_() and dlg == QtWidgets.QMessageBox.Ok:
            return

    def export(self):
        '''
        Exports the results to a xlsx file
        '''
        exportConfigHandler = ConfigurationHandlerFactory.getExportHandler()
        lastOptions= exportConfigHandler.getAll()
        dlg = ExportDialog(self._mainWindow, lastOptions)
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
            excelWriter = ExcelWriter(output, self._configs, newOptions)
            self._analyser.setIons(self.getIonList())
            try:
                excelWriter.toExcel(self._analyser, self._intensityModeller, self._propStorage,
                                    self._libraryBuilder.getFragmentLibrary(), self._settings, self._spectrumHandler,
                                    self._info.toString())
                print("********** saved in:", output, "**********\n")
                try:
                    subprocess.call(['open', output])
                except:
                    pass
            except KeyError as e:
                print(e.__str__(), 'not found')
                dlg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Information, 'Inaccurate Fragment List',
                                            e.__str__() + ' not found\n' +
                                        'The fragmentation pattern or the modification pattern was altered. '
                                        'Please change the corresponding values to the original ones (see info file) and '
                                        'reload the analysis.', QtWidgets.QMessageBox.Ok, self._mainWindow, )
                if dlg.exec_() and dlg == QtWidgets.QMessageBox.Ok:
                    return


    def close(self):
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
            df.to_clipboard(index=False,header=True)

    '''def showLogFile(self):
        self._infoView.show()'''

    def getIonList(self):
        return list(self._intensityModeller.getObservedIons().values())

    def showFragmentation(self):
        self._analyser.setIons(self.getIonList())
        fragmentationView = FragmentationTable([(type,val) for type,val in
                                                self._analyser.calculateRelAbundanceOfSpecies().items()])
        self._openWindows.append(fragmentationView)

    def showOccupancyPlot(self):
        '''
        Makes a widget with the occupancy plot and a table with the corresponding values
        '''
        #dlg = QtWidgets.QInputDialog()
        modification,ok = QtWidgets.QInputDialog.getText(self._mainWindow,'Occupancy Plot', 'Enter the modification: ',
                                                         text=self._propStorage.getModificationName())
        if ok and modification!='':
            self._analyser.setIons(self.getIonList())
            percentageDict = self._analyser.calculateOccupancies(self._configs.get('interestingIons'), modification,
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
            plotFactory.showOccupancyPlot(self._propStorage.getSequenceList(), forwardVals, backwardVals,
                                          self._settings['nrMod'], modification)
            occupView = PlotTableView(self._analyser.toTable(forwardVals.values(), backwardVals.values()),
                                           list(percentageDict.keys()), 'Occupancies: '+modification, 3,
                                      self._analyser.getModificationLoss())
            self._openWindows.append(occupView)


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
        self._analyser.setIons(self._intensityModeller.getObservedIons().values())
        coverages, calcCoverages, overall = self._analyser.getSequenceCoverage(self._propStorage.getFragmentsByDir(1))
        print(coverages, calcCoverages, overall)
        [print(i+1,overall[i][0],overall[i][1], len(self._propStorage.getSequenceList())-(i+1))
         for i in range(len(self._propStorage.getSequenceList())-1)]

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
        searchService.saveSearch(self._savedName, self._settings, self._intensityModeller.getObservedIons().values(),
                                 self._intensityModeller.getDeletedIons().values(),
                                 self._intensityModeller.getRemodelledIons(),
                                 self._spectrumHandler.getSearchedChargeStates(), self._info)
        self._saved = True
        print('done')
        self._infoView.update()