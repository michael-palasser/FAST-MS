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
from src.Exceptions import UnvalidIsotopePatternException
from src.repositories.ConfigurationHandler import ConfigurationHandlerFactory
from src.repositories.IsotopePatternRepository import IsotopePatternReader
from src.top_down.Analyser import Analyser
from src.top_down.SearchProperties import PropertyStorage
from src.top_down.LibraryBuilder import FragmentLibraryBuilder
from src.top_down.SpectrumHandler import SpectrumHandler
from src.top_down.IntensityModeller import IntensityModeller
from src.top_down.ExcelWriter import ExcelWriter
from src.views.CheckIonView import CheckMonoisotopicOverlapView, CheckOverlapsView
from src.views.ResultView import IonTableModel, PeakView, PlotTableView
from src.views.SequencePlots import PlotFactory
from src.views.SimpleDialogs import ExportDialog
from src.views.ParameterDialogs import TDStartDialog
from src.views.SpectrumView import SpectrumView


def sortIonsByName(ionList):
    #return sorted(ionList,key=lambda obj:(obj.type ,obj.number))
    return sorted(ionList, key=lambda obj: (obj.getName(), obj.charge))



#if __name__ == '__main__':
class TD_MainController(object):
    def __init__(self, mainWindow):
        dialog = TDStartDialog(None)
        dialog.exec_()
        if dialog.canceled:
            return
        self.settings = dialog.newSettings
        self.configs = ConfigurationHandlerFactory.getTD_ConfigHandler().getAll()
        if self.search() == 0:
            self.setUpUi(mainWindow)


    def search(self):
        print("\n********** Creating fragment library **********")
        self._propStorage = PropertyStorage(self.settings['sequName'], self.settings['fragmentation'],
                        self.settings['modifications'])
        self.libraryBuilder = FragmentLibraryBuilder(self._propStorage, self.settings['nrMod'])
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
                    return 1
                    #sys.exit()
        if libraryImported == False:
            print("\n********** Writing new list of isotope patterns to:", patternReader.getFile(), "**********\n")
            start = time.time()
            patternReader.saveIsotopePattern(self.libraryBuilder.addNewIsotopePattern())
            print("\ndone\nexecution time: ", round((time.time() - start) / 60, 2), "min\n")

        #ToDo
        """Importing spectral pattern"""
        if self.settings['spectralData'] == '':
            return 1
        #spectralFile = os.path.join(path, 'Spectral_data','top-down', self.settings['spectralData'])
        print("\n********** Importing spectral pattern from:", self.settings['spectralData'], "**********")
        self.spectrumHandler = SpectrumHandler(self.settings['spectralData'], self._propStorage,
                  self.libraryBuilder.getFragmentLibrary(), self.libraryBuilder.getPrecursor(), self.settings)

        """Finding fragments"""
        print("\n********** Search for spectrum **********")
        start = time.time()
        self.spectrumHandler.findPeaks()
        print("\ndone\nexecution time: ", round((time.time() - start) / 60, 3), "min\n")

        self._intensityModeller = IntensityModeller(self.configs)
        start = time.time()
        print("\n********** Calculating relative abundances **********")
        for ion in self.spectrumHandler.foundIons:
            self._intensityModeller.processIons(ion)
        for ion in self.spectrumHandler.ionsInNoise:
            self._intensityModeller.processNoiseIons(ion)
        print("\ndone\nexecution time: ", round((time.time() - start) / 60, 3), "min\n")

        """Handle spectrum with same monoisotopic peak and charge"""
        print("\n********** Handling overlaps **********")
        sameMonoisotopics = self._intensityModeller.findSameMonoisotopics()
        if len(sameMonoisotopics) > 0:
            view = CheckMonoisotopicOverlapView(sameMonoisotopics, self.spectrumHandler.getSpectrum())
            print("User Input requested")
            view.exec_()
            if view and not view.canceled:
                self._intensityModeller.deleteSameMonoisotopics(view.getDumplist())
            else:
                return 1

        """remodelling overlaps"""
        print("\n********** Re-modelling overlaps **********")
        complexPatterns = self._intensityModeller.findOverlaps()
        if len(complexPatterns) > 0:
            view = CheckOverlapsView(complexPatterns, self.spectrumHandler.getSpectrum())
            print("User Input requested")
            view.exec_()
            if view and not view.canceled:
                self._intensityModeller.remodelComplexPatterns(complexPatterns, view.getDumplist())
            else:
                return 1
        self._analyser = Analyser(None, self._propStorage.getSequenceList(),
                                 self.settings['charge'], self._propStorage.getModification())
        print("done")
        return 0

    def setUpUi(self, parent):
        self.saved = False
        self.mainWindow = QtWidgets.QMainWindow(parent)
        self.mainWindow.setObjectName("Results")
        self._translate = QtCore.QCoreApplication.translate
        self.mainWindow.setWindowTitle(self._translate(self.mainWindow.objectName(), self.mainWindow.objectName()))
        self.centralwidget = QtWidgets.QWidget(self.mainWindow)
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        # self.verticalLayout.addWidget(self.tabWidget)
        self.mainWindow.setCentralWidget(self.centralwidget)
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.createMenuBar()
        self.tables = []
        for table, name in zip((self._intensityModeller.getObservedIons(), self._intensityModeller.getDeletedIons()),
                               ('Observed Ions', 'Deleted Ions')):
            self.makeTabWidget(table, name)
        self.verticalLayout.addWidget(self.tabWidget)
        self.mainWindow.resize(1000, 900)
        self.mainWindow.show()

    def createMenuBar(self):
        self.menubar = QtWidgets.QMenuBar(self.mainWindow)
        self.mainWindow.setMenuBar(self.menubar)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 340, 22))
        self.createMenu("File", {'Save': self.dumb, 'Export': self.export,
                                 'Close': self.close}, ['', '', ''], ["Ctrl+S", '', "Ctrl+Q"])
        self.createMenu("Edit", {'Repeat ovl. modelling': self.repeatModellingOverlaps},
                        ['Repeat overlap modelling involving user inputs'], [""])
        self.createMenu("Show",
                {'Occupancy-Plot': self.showOccupancyPlot, 'Charge-Plot': self.showChargeDistrPlot, 'Sequence Coverage': self.dumb,
                 'Original Values':self.showRemodelledIons},
                ['Show occupancies as a function of sequence pos.', 'Show av. charge as a function of sequence pos.',
                 'Show sequence coverage', 'Show original values of overlapping ions'], ["", "", '', ''])

    def createMenu(self, name, options, tooltips, shortcuts):
        menu = QtWidgets.QMenu(self.menubar)
        menu.setTitle(self._translate(self.mainWindow.objectName(), name))
        #menuActions = dict()
        pos = len(options)
        for i, option in enumerate(options.keys()):
            action = QtWidgets.QAction(self.mainWindow)
            action.setText(self._translate(self.mainWindow.objectName(),option))
            if tooltips[i] != "":
                action.setToolTip(tooltips[i])
            if shortcuts[i] != "":
                action.setShortcut(shortcuts[i])
            action.triggered.connect(options[option])
            #menuActions[option] = action
            menu.addAction(action)
            pos -= 1
        self.menubar.addAction(menu.menuAction())
        return menu#, menuActions

    def fillUi(self):
        self.tables = []
        for table, name in zip((self._intensityModeller.getObservedIons(), self._intensityModeller.getDeletedIons()),
                               ('Observed Ions', 'Deleted Ions')):
            self.makeTabWidget(table, name)
        self.verticalLayout.addWidget(self.tabWidget)

    def makeTabWidget(self, data, name):
        tab = QtWidgets.QWidget()
        verticalLayout = QtWidgets.QVBoxLayout(self.mainWindow)
        tab.setLayout(verticalLayout)
        self.tabWidget.addTab(tab, "")
        self.tabWidget.setTabText(self.tabWidget.indexOf(tab), self._translate(self.mainWindow.objectName(), name))
        scrollArea,table = self.makeScrollArea(tab,[ion.getMoreValues() for ion in data.values()])
        verticalLayout.addWidget(scrollArea)
        self.tables.append(table)
        self.tabWidget.setEnabled(True)
        #self.tabWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        #tab.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        # scrollArea.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

    def makeScrollArea(self, parent, data):
        scrollArea = QtWidgets.QScrollArea(parent)
        #scrollArea.setGeometry(QtCore.QRect(10, 10, 1150, 800))
        scrollArea.setWidgetResizable(True)
        # scrollArea.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        # scrollArea.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        table = self.makeTable(scrollArea, data)

        table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        table.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        scrollArea.setWidget(table)
        return scrollArea, table

    def makeTable(self, parent, data):
        tableModel = IonTableModel(data,
                   self._intensityModeller.getPrecRegion(self.settings['sequName'], abs(self.settings['charge'])),
                   self.configs['shapeMarked'], self.configs['scoreMarked'])
        """self.proxyModel = QSortFilterProxyModel()
        self.proxyModel.setSourceModel(model)"""
        table = QtWidgets.QTableView(parent)
        table.setModel(tableModel)
        table.setSortingEnabled(True)
        #table.setModel(self.proxyModel)
        self.connectTable(table)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        table.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        return table


    def connectTable(self, table):
        table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        table.customContextMenuRequested['QPoint'].connect(partial(self.showOptions, table))

    def showOptions(self, table, pos):
        menu = QtWidgets.QMenu()
        showAction = menu.addAction("Show in Spectrum")
        peakAction = menu.addAction("Show Peaks")
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
            #global spectrumView
            ajacentIons, minLimit, maxLimit  = self._intensityModeller.getAdjacentIons(selectedHash)
            #minWindow, maxWindow, maxY = self._intensityModeller.getLimits(ajacentIons)
            peaks = self.spectrumHandler.getSpectrum(minLimit-1, maxLimit+1)
            spectrumView = SpectrumView(self.mainWindow, peaks, ajacentIons, np.min(selectedIon.isotopePattern['m/z']),
                                np.max(selectedIon.isotopePattern['m/z']), np.max(selectedIon.isotopePattern['relAb']))
        elif action == peakAction:
            #global peakview
            PeakView(self.mainWindow, selectedIon, self._intensityModeller.remodelSingleIon, self.saveSingleIon)

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
                self._intensityModeller.switchIon(selectedIon)
                table.model().removeData(selectedRow)
                self.tables[other].model().addData(selectedIon.getMoreValues())
                print(actionStrings[mode]+"d",selectedRow, selectedHash)





    def saveSingleIon(self, newIon):
        newIonHash = self._intensityModeller.getHash(newIon)
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
                self._intensityModeller.addRemodelledIon(oldIon)
                newIon.comment += 'man.mod.'
                ionDict[newIonHash] = newIon
                self.tables[index].model().updateData(newIon.getMoreValues())
                print('Saved', newIon.getName(),',', newIon.charge)



    def repeatModellingOverlaps(self):
        self._intensityModeller.findOverlaps(20)
        self.verticalLayout.removeWidget(self.tabWidget)
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
            if dlg.getFormat() == 'xlsx':
                """"filename = dlg.getFilename()
                if filename == '':
                    output = self.settings['spectralData'][0:-4] + '_out' + '.xlsx'
                if filename[-5:]!= 'xlsx':
                    filename+='xlsx'"""
                self.toExcel(dlg.getDir(),dlg.getFilename())
            else:
                self.dumb()


    def toExcel(self, outputPath, filename): #ToDo
        """output"""
        if filename == '':
            inputFileName = os.path.split(self.settings['spectralData'])[-1]
            filename = inputFileName[0:-4] + '_out' + '.xlsx'
        elif filename[-5:] != '.xlsx':
            filename += '.xlsx'
        if outputPath == '':
            outputPath = os.path.join(path, 'Spectral_data','top-down')
        output = os.path.join(outputPath, filename)
        excelWriter = ExcelWriter(output, self.configs)
        self._analyser.setIons(list(self._intensityModeller.getObservedIons().values()))
        excelWriter.toExcel(self._analyser, self._intensityModeller, self._propStorage,
                            self.libraryBuilder.getFragmentLibrary(), self.settings, self.spectrumHandler)
        print("********** saved in:", output, "**********\n")
        try:
            subprocess.call(['open',output])
        except:
            pass

    def close(self):
        message = ''
        if self.saved == False:
            message = 'Warning: Results not saved.\n'
        choice = QtWidgets.QMessageBox.question(self.mainWindow, 'Close Search',
                                                message + "Do you really want to close the search?",
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if choice == QtWidgets.QMessageBox.Yes:
            self.mainWindow.close()

    def showRemodelledIons(self):
        self._remView = QtWidgets.QWidget()
        #title = 'Original Values of Overlapping Ions'
        self._remView._translate = QtCore.QCoreApplication.translate
        self._remView.setWindowTitle(self._translate(self._remView.objectName(), 'Original Values of Overlapping Ions'))
        ions = self._intensityModeller.getRemodelledIons()
        verticalLayout = QtWidgets.QVBoxLayout(self._remView)
        scrollArea, table = self.makeScrollArea(self._remView, [ion.getMoreValues() for ion in ions])
        table.customContextMenuRequested['QPoint'].connect(partial(self.showRedOptions, table))
        verticalLayout.addWidget(scrollArea)
        self._remView.resize(1000, 750)
        self._remView.show()

    def showRedOptions(self, table, pos):
        menu = QtWidgets.QMenu()
        showAction = menu.addAction("Show in Spectrum")
        peakAction = menu.addAction("Show Peaks")
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
            ajacentIons, minLimit, maxLimit  = self._intensityModeller.getAdjacentIons(selectedHash)
            ajacentIons = [ion for ion in ajacentIons if self._intensityModeller.getHash(ion)!=selectedHash]
            peaks = self.spectrumHandler.getSpectrum(minLimit-1, maxLimit+1)
            SpectrumView(self.mainWindow, peaks, [selectedIon]+ajacentIons, np.min(selectedIon.isotopePattern['m/z']),
                                np.max(selectedIon.isotopePattern['m/z']), np.max(selectedIon.isotopePattern['relAb']))
        elif action == peakAction:
            PeakView(self.mainWindow, selectedIon, self._intensityModeller.remodelSingleIon, self.saveSingleIon)
        elif action == copyRowAction:
            df=pd.DataFrame(data=[table.model().getRow(selectedRow)], columns=table.model().getHeaders())
            df.to_clipboard(index=False,header=True)
        elif action == copyTableAction:
            df=pd.DataFrame(data=table.model().getData(), columns=table.model().getHeaders())
            df.to_clipboard(index=False,header=True)


    def showOccupancyPlot(self):
        self._analyser.setIons(list(self._intensityModeller.getObservedIons().values()))
        percentageDict = self._analyser.calculatePercentages(self.configs['interestingIons'])
        if percentageDict == None:
            dlg = QtWidgets.QMessageBox(parent=self.mainWindow, title='Unvalid Request',
                        text='It is not possible to calculate occupancies for an unmodified molecule.',
                        icon=QtWidgets.QMessageBox.Information, buttons=QtWidgets.QMessageBox.Ok)
            if dlg == QtWidgets.QMessageBox.Ok:
                return

        plotFactory = PlotFactory(self.mainWindow)
        forwardVals = self.libraryBuilder.filterByDir(percentageDict,1)
        backwardVals = self.libraryBuilder.filterByDir(percentageDict,-1)
        plotFactory.showOccupancyPlot(self.libraryBuilder.getSequenceList(), forwardVals, backwardVals,
                                      self.settings['nrMod'])
        self.occupView = PlotTableView(self._analyser.toTable(forwardVals.values(), backwardVals.values()),
                                       list(percentageDict.keys()), 'Occupancies', 3)


    def showChargeDistrPlot(self):
        self._analyser.setIons(list(self._intensityModeller.getObservedIons().values()))
        chargeDict, redChargeDict = self._analyser.getAvCharges(self.configs['interestingIons'])
        plotFactory1 = PlotFactory(self.mainWindow)
        #plotFactory2 = PlotFactory(self.mainWindow)
        forwardVals = self.libraryBuilder.filterByDir(chargeDict,1)
        backwardVals = self.libraryBuilder.filterByDir(chargeDict,-1)
        plotFactory1.showChargePlot(self.libraryBuilder.getSequenceList(), forwardVals, backwardVals,
                                    self.settings['charge'])

        self.chargeView = PlotTableView(self._analyser.toTable(forwardVals.values(), backwardVals.values()),
                                       list(chargeDict.keys()), 'Av. Charge per Fragment', 1)
        '''plotFactory2.showChargePlot(self.libraryBuilder.getSequenceList(),
                                      self.libraryBuilder.filterByDir(redChargeDict,1),
                                      self.libraryBuilder.filterByDir(redChargeDict,-1),self.settings['charge'])'''