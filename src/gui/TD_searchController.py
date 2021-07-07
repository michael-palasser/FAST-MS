'''
Created on 21 Jul 2020

@author: michael
'''

import subprocess
import traceback
import os

import numpy as np
import time
from functools import partial
import pandas as pd
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QAbstractItemView

from src import path
from src.Exceptions import InvalidIsotopePatternException, InvalidInputException
from src.entities.Info import Info
from src.gui.AbstractMainWindows import SimpleMainWindow
from src.gui.InfoView import InfoView
from src.repositories.ConfigurationHandler import ConfigurationHandlerFactory
from src.repositories.IsotopePatternRepository import IsotopePatternRepository
from src.top_down.Analyser import Analyser
from src.entities.SearchSettings import SearchSettings
from src.top_down.LibraryBuilder import FragmentLibraryBuilder
from src.top_down.SearchService import SearchService
from src.top_down.SpectrumHandler import SpectrumHandler
from src.top_down.IntensityModeller import IntensityModeller
from src.top_down.ExcelWriter import ExcelWriter
from src.gui.CheckIonView import CheckMonoisotopicOverlapView, CheckOverlapsView
from src.gui.ResultView import IonTableModel
from src.gui.PlotTables import PlotTableView
from src.gui.PeakViews import PeakView, SimplePeakView
from src.gui.SequencePlots import PlotFactory
from src.gui.SimpleDialogs import ExportDialog, SelectSearchDlg, OpenSpectralDataDlg, SaveSearchDialog
#from src.gui.ParameterDialogs import TDStartDialog
from src.gui.StartDialogs import TDStartDialog
from src.gui.SpectrumView import SpectrumView


def sortIonsByName(ionList):
    #return sorted(ionList,key=lambda obj:(obj.type ,obj.number))
    return sorted(ionList, key=lambda obj: (obj.getName(), obj.getCharge()))



#if __name__ == '__main__':
class TD_MainController(object):
    '''
    Controller class for starting, saving, exporting and loading a top-down search/analysis
    '''
    def __init__(self, parent, new):
        if new:
            dialog = TDStartDialog(None)
            dialog.exec_()
            if dialog.canceled:
                return
            self.settings = dialog.newSettings
            self.configs = ConfigurationHandlerFactory.getTD_ConfigHandler().getAll()
            self._propStorage = SearchSettings(self.settings['sequName'], self.settings['fragmentation'],
                                               self.settings['modifications'])
            self._info = Info(self.settings, self.configs, self._propStorage)
            self.saved = False
            self._savedName = os.path.split(self.settings['spectralData'])[-1][:-4]
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
            if dialog.exec_() and not dialog.canceled:
                self.configs = ConfigurationHandlerFactory.getTD_ConfigHandler().getAll()
                self.settings, observedIons, delIons, remIons, searchedZStates, logFile = \
                    searchService.getSearch(dialog.getName())
                self._info = Info(logFile)
                self._savedName = dialog.getName()
                if not os.path.isfile(self.settings['spectralData']):
                    dlg = OpenSpectralDataDlg(parent)
                    if dlg.exec_() and not dlg.canceled:
                        self.settings['spectralData'] = dlg.getValue()
                self._propStorage = SearchSettings(self.settings['sequName'], self.settings['fragmentation'],
                                                   self.settings['modifications'])
                self.libraryBuilder = FragmentLibraryBuilder(self._propStorage, self.settings['nrMod'])
                self.libraryBuilder.createFragmentLibrary()

                self.spectrumHandler = SpectrumHandler(self._propStorage, self.libraryBuilder.getPrecursor(), self.settings)
                self.spectrumHandler.setSearchedChargeStates(searchedZStates)
                self._intensityModeller = IntensityModeller(self.configs)
                self._intensityModeller.setIonLists(observedIons, delIons, remIons)
                self._analyser = Analyser(None, self._propStorage.getSequenceList(), self.settings['charge'],
                                          self._propStorage.getModificationName())
                self.saved = True
                self.setUpUi(parent)

    @staticmethod
    def deleteSearch(name, searchService):
        searchService.deleteSearch(name)


    def search(self):
        print("\n********** Creating fragment library **********")
        self.libraryBuilder = FragmentLibraryBuilder(self._propStorage, self.settings['nrMod'])
        self.libraryBuilder.createFragmentLibrary()

        """read existing ion-list file or create new one"""
        libraryImported = False
        patternReader = IsotopePatternRepository()
        if self.settings['fragLib'] != '':
            settings = [self.settings['fragLib']]
        else:
            settings = [self.settings[setting] for setting in ['sequName','fragmentation', 'nrMod', 'modifications']]
        if patternReader.findFile(settings):
            print("\n********** Importing list of isotope patterns from:", patternReader.getFile(), "**********")
            try:
                self.libraryBuilder.setFragmentLibrary(patternReader)
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
            patternReader.saveIsotopePattern(self.libraryBuilder.addNewIsotopePattern())
            print("\ndone\nexecution time: ", round((time.time() - start) / 60, 2), "min\n")

        """Importing spectral pattern"""
        if self.settings['spectralData'] == '':
            return 1
        #spectralFile = os.path.join(path, 'Spectral_data','top-down', self.settings['spectralData'])
        print("\n********** Importing spectral pattern from:", self.settings['spectralData'], "**********")
        self.spectrumHandler = SpectrumHandler(self._propStorage, self.libraryBuilder.getPrecursor(), self.settings)
        """Finding fragments"""
        print("\n********** Search for ions **********")
        start = time.time()
        self.spectrumHandler.findIons(self.libraryBuilder.getFragmentLibrary())
        print("\ndone\nexecution time: ", round((time.time() - start) / 60, 3), "min\n")

        self._intensityModeller = IntensityModeller(self.configs)
        start = time.time()
        print("\n********** Calculating relative abundances **********")
        for ion in self.spectrumHandler.getFoundIons():
            self._intensityModeller.processIons(ion)
        for ion in self.spectrumHandler._ionsInNoise:
            self._intensityModeller.processNoiseIons(ion)
        self.spectrumHandler.emptyLists()
        print("\ndone\nexecution time: ", round((time.time() - start) / 60, 3), "min\n")

        """Handle ions with same monoisotopic peak and charge"""
        print("\n********** Handling overlaps **********")
        sameMonoisotopics = self._intensityModeller.findSameMonoisotopics()
        print('mono', sameMonoisotopics)
        if len(sameMonoisotopics) > 0:
            view = CheckMonoisotopicOverlapView(sameMonoisotopics, self.spectrumHandler.getSpectrum())
            print("User Input requested")
            view.exec_()
            if view and not view.canceled:
                dumpList = view.getDumplist()
                [self._info.deleteMonoisotopic(ion) for ion in dumpList]
                self._intensityModeller.deleteSameMonoisotopics(dumpList)
            else:
                return 1

        """remodelling overlaps"""
        print("\n********** Re-modelling overlaps **********")
        complexPatterns = self._intensityModeller.remodelOverlaps()
        if len(complexPatterns) > 0:
            view = CheckOverlapsView(complexPatterns, self.spectrumHandler.getSpectrum())
            print("User Input requested")
            view.exec_()
            if view and not view.canceled:
                dumpList = view.getDumplist()
                [self._info.deleteIon(ion) for ion in dumpList]
                self._intensityModeller.remodelComplexPatterns(complexPatterns, dumpList)
            else:
                return 1
        self._analyser = Analyser(None, self._propStorage.getSequenceList(),
                                 self.settings['charge'], self._propStorage.getModificationName())
        self._info.searchFinished(self.spectrumHandler.getUpperBound())
        print("done")
        return 0

    def setUpUi(self, parent):
        self._openWindows = []
        self.mainWindow = SimpleMainWindow(parent, 'Results:  ' + os.path.split(self.settings['spectralData'])[-1])
        self._translate = QtCore.QCoreApplication.translate
        self.centralwidget = self.mainWindow.centralWidget()
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self._infoView = InfoView(None, self._info)
        self.createMenuBar()
        self.tables = []
        for data, name in zip((self._intensityModeller.getObservedIons(), self._intensityModeller.getDeletedIons()),
                               ('Observed Ions', 'Deleted Ions')):
            self.makeTabWidget(data, name)
        self.verticalLayout.addWidget(self.tabWidget)
        self.mainWindow.resize(1000, 900)
        self.mainWindow.show()

    def createMenuBar(self):
        self.mainWindow.createMenuBar()
        self._actions = dict()
        _,actions = self.mainWindow.createMenu("File", {'Save': (self.saveAnalysis,None,"Ctrl+S"),
                                'Export': (self.export,None,None), 'Close': (self.close,None,"Ctrl+Q")}, None)
        self._actions.update(actions)
        _,actions = self.mainWindow.createMenu("Edit", {'Repeat ovl. modelling':
                            (self.repeatModellingOverlaps,'Repeat overlap modelling involving user inputs',None)},None)
        self._actions.update(actions)
        _,actions = self.mainWindow.createMenu("Show",
                {'Results': (self.mainWindow.show,'Show lists of observed and deleted ions',None),
                 'Occupancy-Plot': (self.showOccupancyPlot,'Show occupancies as a function of sequence pos.',None),
                 'Charge-Plot': (lambda: self.showChargeDistrPlot(False),'Show av. charge as a function of sequence pos. (Calculated with Int. values)',None),
                 'Reduced Charge-Plot':(lambda: self.showChargeDistrPlot(True),'Show av. charge as a function of sequence pos. (Calculated with Int./z values)',None),
                 'Sequence Coverage': (self.dumb,'Show sequence coverage',None),
                 'Original Values':(self.showRemodelledIons,'Show original values of overlapping ions',None),
                 'Info File':(self._infoView.show,'Show Protocol',None)},None)
        self._actions.update(actions)
        if self.settings['modifications'] == '-':
            self._actions['Occupancy-Plot'].setDisabled(True)
        if len(self.configs['interestingIons'])<1:
            for action in ['Occupancy-Plot','Charge-Plot','Reduced Charge-Plot']:
                self._actions[action].setDisabled(True)
                self._actions[action].setToolTip('Choose ions of interest within "Edit Parameters" menu to use this function')


    def fillUi(self):
        self.tables = []
        for table, name in zip((self._intensityModeller.getObservedIons(), self._intensityModeller.getDeletedIons()),
                               ('Observed Ions', 'Deleted Ions')):
            self.makeTabWidget(table, name)
        self.verticalLayout.addWidget(self.tabWidget)

    def makeTabWidget(self, data, name):
        tab = QtWidgets.QWidget()
        verticalLayout = QtWidgets.QVBoxLayout(tab)
        #tab.setLayout(verticalLayout)
        self.tabWidget.addTab(tab, "")
        self.tabWidget.setTabText(self.tabWidget.indexOf(tab), self._translate(self.mainWindow.objectName(), name))
        scrollArea,table = self.makeScrollArea(tab,[ion.getMoreValues() for ion in data.values()], self.showOptions)
        verticalLayout.addWidget(scrollArea)
        self.tables.append(table)
        self.tabWidget.setEnabled(True)
        #self.tabWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        #tab.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        # scrollArea.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

    def makeScrollArea(self, parent, data, fun):
        scrollArea = QtWidgets.QScrollArea(parent)
        #scrollArea.setGeometry(QtCore.QRect(10, 10, 1150, 800))
        scrollArea.setWidgetResizable(True)
        # scrollArea.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        # scrollArea.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        table = self.makeTable(scrollArea, data, fun)

        table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        table.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        scrollArea.setWidget(table)
        return scrollArea, table

    def makeTable(self, parent, data,fun):
        tableModel = IonTableModel(data,
                   self._intensityModeller.getPrecRegion(self.settings['sequName'], abs(self.settings['charge'])),
                   self.configs['shapeMarked'], self.configs['scoreMarked'])
        """self.proxyModel = QSortFilterProxyModel()
        self.proxyModel.setSourceModel(model)"""
        table = QtWidgets.QTableView(parent)
        table.setModel(tableModel)
        table.setSortingEnabled(True)
        #table.setModel(self.proxyModel)
        table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        table.customContextMenuRequested['QPoint'].connect(partial(fun, table))
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        table.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        return table



    def showOptions(self, table, pos):
        menu = QtWidgets.QMenu()
        showAction = menu.addAction("Show in Spectrum")
        peakAction = menu.addAction("Show Peaks")
        formulaAction = menu.addAction("Get Formula")
        copyRowAction = menu.addAction("Copy Row")
        copyTableAction = menu.addAction("Copy Table")
        actionStrings = ["Delete", "Restore"]
        mode = 0
        other = 1
        if table != self.tables[0]:
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
            peaks = self.spectrumHandler.getSpectrum(minLimit-1, maxLimit+1)
            spectrumView = SpectrumView(None, peaks, ajacentIons, np.min(selectedIon.getIsotopePattern()['m/z']),
                                np.max(selectedIon.getIsotopePattern()['m/z']),
                                        np.max(selectedIon.getIsotopePattern()['relAb']))
            self._openWindows.append(spectrumView)
        elif action == peakAction:
            #global peakview
            self._openWindows.append(PeakView(self.mainWindow, selectedIon, self._intensityModeller.remodelSingleIon, self.saveSingleIon))
        elif action == formulaAction:
            text = 'Ion:\t' + selectedIon.getName()+\
                   '\n\nFormula:\t'+selectedIon.getFormula().toString()
            QtWidgets.QMessageBox.information(self.mainWindow, selectedIon.getName(), text, QtWidgets.QMessageBox.Ok)
        elif action == copyRowAction:
            df=pd.DataFrame(data=[table.model().getRow(selectedRow)], columns=table.model().getHeaders())
            df.to_clipboard(index=False,header=True)
        elif action == copyTableAction:
            df=pd.DataFrame(data=table.model().getData(), columns=table.model().getHeaders())
            df.to_clipboard(index=False,header=True)
        elif action == delAction:
            choice = QtWidgets.QMessageBox.question(self.mainWindow, "",
                                        actionStrings[mode][:-1]+'ing '+selectedIon.getName()+"?",
                                        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if choice == QtWidgets.QMessageBox.Yes:
                if mode ==0:
                    self._info.deleteIon(selectedIon)
                else:
                    self._info.restoreIon(selectedIon)
                self._infoView.update()
                self.saved = False
                self._intensityModeller.switchIon(selectedIon)
                table.model().removeData(selectedRow)
                self.tables[other].model().addData(selectedIon.getMoreValues())
                print(actionStrings[mode]+"d",selectedRow, selectedHash)



    def saveSingleIon(self, newIon):
        newIonHash = newIon.getHash()
        if newIonHash in self._intensityModeller.getObservedIons():
            ionDict = self._intensityModeller.getObservedIons()
            index = 0
        else:
            ionDict = self._intensityModeller.getDeletedIons()
            index = 1
        oldIon = ionDict[newIonHash]
        if oldIon.getIntensity() != newIon.getIntensity():
            choice = QtWidgets.QMessageBox.question(self.mainWindow, 'Saving Ion',
                                                    "Please confirm to change the values of ion: " + oldIon.getId(),
                                                    QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
            if choice == QtWidgets.QMessageBox.Ok:
                self._info.changeIon(oldIon, newIon)
                self._infoView.update()
                self.saved = False
                self._intensityModeller.addRemodelledIon(oldIon)
                newIon.addComment('man.mod.')
                ionDict[newIonHash] = newIon
                self.tables[index].model().updateData(newIon.getMoreValues())
                print('Saved', newIon.getId())



    def repeatModellingOverlaps(self):
        self._info.repeatModelling()
        self.saved = False
        self._intensityModeller.remodelOverlaps(True)
        self.verticalLayout.removeWidget(self.tabWidget)
        self.tabWidget.hide()
        del self.tabWidget
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.fillUi()

    def dumb(self):
        print('not yet implemented')
        dlg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Information, 'Unvalid Request',
                    'Sorry, not implemented yet', QtWidgets.QMessageBox.Ok, self.mainWindow, )
        if dlg.exec_() and dlg == QtWidgets.QMessageBox.Ok:
            return

    def export(self):
        dlg = ExportDialog(self.mainWindow)
        dlg.exec_()
        if dlg and not dlg.canceled:
            self._info.export()
            outputPath, filename = dlg.getDir(), dlg.getFilename()
            if filename == '':
                inputFileName = os.path.split(self.settings['spectralData'])[-1]
                filename = inputFileName[0:-4] + '_out' + '.xlsx'
            elif filename[-5:] != '.xlsx':
                filename += '.xlsx'
            if outputPath == '':
                outputPath = os.path.join(path, 'Spectral_data', 'top-down')
            output = os.path.join(outputPath, filename)
            excelWriter = ExcelWriter(output, self.configs)
            self._analyser.setIons(list(self._intensityModeller.getObservedIons().values()))
            try:
                excelWriter.toExcel(self._analyser, self._intensityModeller, self._propStorage,
                                    self.libraryBuilder.getFragmentLibrary(), self.settings, self.spectrumHandler,
                                    self._info.toString())
                print("********** saved in:", output, "**********\n")
                try:
                    subprocess.call(['open', output])
                except:
                    pass
            except KeyError as e:
                print(e.__str__(), 'not found')
                dlg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Information, 'Inaccurate Fragment List',
                                            e.__str__()+ ' not found\n'+
                                        'The fragmentation pattern or the modification pattern was altered. '
                                        'Please change the corresponding values to the original ones (see info file) and '
                                        'reload the analysis.', QtWidgets.QMessageBox.Ok, self.mainWindow, )
                if dlg.exec_() and dlg == QtWidgets.QMessageBox.Ok:
                    return


    def close(self):
        message = ''
        if self.saved == False:
            message = 'Warning: Unsaved Results\n'
        choice = QtWidgets.QMessageBox.question(self.mainWindow, 'Close Search',
                                                message + "Do you really want to close the analysis?",
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if choice == QtWidgets.QMessageBox.Yes:
            [w.close() for w in self._openWindows]
            self.mainWindow.close()
            self._infoView.close()

    def showRemodelledIons(self):
        remView = QtWidgets.QWidget()
        #title = 'Original Values of Overlapping Ions'
        remView._translate = QtCore.QCoreApplication.translate
        remView.setWindowTitle(self._translate(remView.objectName(), 'Original Values of Overlapping Ions'))
        ions = self._intensityModeller.getRemodelledIons()
        verticalLayout = QtWidgets.QVBoxLayout(remView)
        scrollArea, table = self.makeScrollArea(remView, [ion.getMoreValues() for ion in ions], self.showRedOptions)
        table.customContextMenuRequested['QPoint'].connect(partial(self.showRedOptions, table))
        verticalLayout.addWidget(scrollArea)
        remView.resize(1000, 750)
        self._openWindows.append(remView)
        remView.show()

    def showRedOptions(self, table, pos):
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
            peaks = self.spectrumHandler.getSpectrum(minLimit-1, maxLimit+1)
            view = SpectrumView(None, peaks, [selectedIon]+ajacentIons, np.min(selectedIon.getIsotopePattern()['m/z']),
                                np.max(selectedIon.getIsotopePattern()['m/z']), np.max(selectedIon.getIsotopePattern()['relAb']))
            self._openWindows.append(view)
        elif action == peakAction:
            #PeakView(self.mainWindow, selectedIon, self._intensityModeller.remodelSingleIon, self.saveSingleIon)
            self._openWindows.append(SimplePeakView(self.mainWindow, selectedIon))
        elif action == formulaAction:
            text = 'Ion:\t' + selectedIon.getName()+\
                   '\n\nFormula:\t'+selectedIon.getFormula().toString()
            QtWidgets.QMessageBox.information(self.mainWindow, selectedIon.getName(), text, QtWidgets.QMessageBox.Ok)
        elif action == copyRowAction:
            df=pd.DataFrame(data=[table.model().getRow(selectedRow)], columns=table.model().getHeaders())
            df.to_clipboard(index=False,header=True)
        elif action == copyTableAction:
            df=pd.DataFrame(data=table.model().getData(), columns=table.model().getHeaders())
            df.to_clipboard(index=False,header=True)

    '''def showLogFile(self):
        self._infoView.show()'''

    def showOccupancyPlot(self):
        self._analyser.setIons(list(self._intensityModeller.getObservedIons().values()))
        percentageDict = self._analyser.calculateOccupancies(self.configs.get('interestingIons'),
                                                             self._propStorage.getUnimportantModifs())
        '''if percentageDict == None:
            dlg = QtWidgets.QMessageBox(self.mainWindow, title='Unvalid Request',
                        text='It is not possible to calculate occupancies for an unmodified molecule.',
                        icon=QtWidgets.QMessageBox.Information, buttons=QtWidgets.QMessageBox.Ok)
            if dlg == QtWidgets.QMessageBox.Ok:
                return'''
        plotFactory = PlotFactory(self.mainWindow)
        forwardVals = self._propStorage.filterByDir(percentageDict,1)
        backwardVals = self._propStorage.filterByDir(percentageDict,-1)
        plotFactory.showOccupancyPlot(self._propStorage.getSequenceList(), forwardVals, backwardVals,
                                      self.settings['nrMod'])
        occupView = PlotTableView(self._analyser.toTable(forwardVals.values(), backwardVals.values()),
                                       list(percentageDict.keys()), 'Occupancies', 3)
        self._openWindows.append(occupView)


    def showChargeDistrPlot(self, reduced):
        self._analyser.setIons(list(self._intensityModeller.getObservedIons().values()))
        chargeDict, minMaxCharges = self._analyser.analyseCharges(self.configs.get('interestingIons'), reduced)
        plotFactory1 = PlotFactory(self.mainWindow)
        #plotFactory2 = PlotFactory(self.mainWindow)
        forwardVals = self._propStorage.filterByDir(chargeDict,1)
        backwardVals = self._propStorage.filterByDir(chargeDict,-1)
        forwardLimits = self._propStorage.filterByDir(minMaxCharges,1)
        backwardLimits = self._propStorage.filterByDir(minMaxCharges,-1)
        plotFactory1.showChargePlot(self._propStorage.getSequenceList(), forwardVals, backwardVals,
                                    self.settings['charge'], forwardLimits, backwardLimits)
        chargeView = PlotTableView(self._analyser.toTable(forwardVals.values(), backwardVals.values()),
                                       list(chargeDict.keys()), 'Av. Charge per Fragment', 1)
        self._openWindows.append(chargeView)
        '''plotFactory2.showChargePlot(self.libraryBuilder.getSequenceList(),
                                      self.libraryBuilder.filterByDir(redChargeDict,1),
                                      self.libraryBuilder.filterByDir(redChargeDict,-1),self.settings['charge'])'''

    def saveAnalysis(self):
        searchService = SearchService()
        names = searchService.getAllSearchNames()
        while True:
            dlg = SaveSearchDialog(self._savedName)
            #name, ok = QtWidgets.QInputDialog.getText(self.mainWindow, 'Save Analysis', 'Enter the name: ')
            if dlg.exec_() and dlg.ok:
                self._savedName = dlg.getText()
                if self._savedName in names:
                    choice = QtWidgets.QMessageBox.question(self.mainWindow, "Overwriting",
                                "There is already a saved analysis with name: "+self._savedName+"\nDo you want to overwrite it?",
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                    if choice == QtWidgets.QMessageBox.Yes:
                        break
                else:
                    break
            else:
                return
        print('Saving analysis', self._savedName)
        self._info.save()
        searchService.saveSearch(self._savedName, self.settings, self._intensityModeller.getObservedIons().values(),
                                 self._intensityModeller.getDeletedIons().values(),
                                 self._intensityModeller.getRemodelledIons(),
                                 self.spectrumHandler.getSearchedChargeStates(), self._info)
        self.saved = True
        print('done')
        self._infoView.update()