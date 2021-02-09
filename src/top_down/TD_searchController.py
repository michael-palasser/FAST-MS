'''
Created on 21 Jul 2020

@author: michael
'''

import os
import subprocess
import traceback
from os.path import join

import numpy as np
import time
from functools import partial
import pandas as pd
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QAbstractItemView


from src.Exceptions import UnvalidIsotopePatternException
from src.repositories.ConfigurationHandler import ConfigurationHandlerFactory
from src.repositories.IsotopePatternRepository import IsotopePatternReader
from src.top_down.Analyser import Analyser
from src.top_down.LibraryBuilder import FragmentLibraryBuilder
from src.top_down.SpectrumHandler import SpectrumHandler
from src.top_down.IntensityModeller import IntensityModeller
from src.top_down.ExcelWriter import ExcelWriter
from src.views.CheckIonView import CheckMonoisotopicOverlapView, CheckOverlapsView
from src.views.ResultView import IonTableModel, PeakView
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

        """Handle spectrum with same monoisotopic peak and charge"""
        print("\n********** Handling overlaps **********")
        sameMonoisotopics = self.intensityModeller.findSameMonoisotopics()
        if len(sameMonoisotopics) > 0:
            view = CheckMonoisotopicOverlapView(sameMonoisotopics, self.spectrumHandler.getSpectrum())
            print("User Input requested")
            view.exec_()
            if view and not view.canceled:
                self.intensityModeller.deleteSameMonoisotopics(view.getDumplist())
            else:
                return 1

        """remodelling overlaps"""
        print("\n********** Re-modelling overlaps **********")
        complexPatterns = self.intensityModeller.findOverlaps()
        if len(complexPatterns) > 0:
            view = CheckOverlapsView(complexPatterns, self.spectrumHandler.getSpectrum())
            print("User Input requested")
            view.exec_()
            if view and not view.canceled:
                self.intensityModeller.remodelComplexPatterns(complexPatterns, view.getDumplist())
            else:
                return 1
        self._analyser = Analyser(self.libraryBuilder.getSequence().getSequenceList(),
                                 self.settings['charge'], self.libraryBuilder.getModification())
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
        for table, name in zip((self.intensityModeller.getObservedIons(), self.intensityModeller.getDeletedIons()),
                               ('Observed Ions', 'Deleted Ions')):
            self.makeTabWidget(table, name)
        self.verticalLayout.addWidget(self.tabWidget)
        self.mainWindow.resize(1200, 900)
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
                {'Occupancy-Plot': self.dumb, 'Charge-Plot': self.dumb, 'Sequence Coverage': self.dumb},
                ['Show occupancies as a function of sequence pos.', 'Show av. charge as a function of sequence pos.',
                 'Show sequence coverage'], ["", "", ''])

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
        for table, name in zip((self.intensityModeller.getObservedIons(), self.intensityModeller.getDeletedIons()),
                               ('Observed Ions', 'Deleted Ions')):
            self.makeTabWidget(table, name)
        self.verticalLayout.addWidget(self.tabWidget)

    def makeTabWidget(self, data, name):
        tab = QtWidgets.QWidget()
        self.tabWidget.addTab(tab, "")
        self.tabWidget.setTabText(self.tabWidget.indexOf(tab), self._translate(self.mainWindow.objectName(), name))
        scrollArea = QtWidgets.QScrollArea(tab)
        scrollArea.setGeometry(QtCore.QRect(10, 10, 1150, 800))
        scrollArea.setWidgetResizable(True)
        #scrollArea.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        #scrollArea.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        table = self.makeTable(scrollArea, data)
        scrollArea.setWidget(table)
        self.tables.append(table)
        self.tabWidget.setEnabled(True)


    def makeTable(self, parent, data):
        tableModel = IonTableModel([ion.getMoreValues() for ion in data.values()])
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
        selectedIon = self.intensityModeller.getIon(selectedHash)
        if action == showAction:
            #global spectrumView
            ajacentIons, minLimit, maxLimit  = self.intensityModeller.getAdjacentIons(selectedHash)
            #minWindow, maxWindow, maxY = self.intensityModeller.getLimits(ajacentIons)
            peaks = self.spectrumHandler.getSpectrum(minLimit-1, maxLimit+1)
            spectrumView = SpectrumView(self.mainWindow, peaks, ajacentIons, np.min(selectedIon.isotopePattern['m/z']),
                                np.max(selectedIon.isotopePattern['m/z']), np.max(selectedIon.isotopePattern['relAb']))
        elif action == peakAction:
            global peakview
            peakview = PeakView(selectedIon.getPeaks())
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
                self.intensityModeller.switchIon(selectedIon)
                table.model().removeData(selectedRow)
                self.tables[other].model().addData(selectedIon.getMoreValues())
                print(actionStrings[mode]+"d",selectedRow, selectedHash)


    def repeatModellingOverlaps(self):
        self.intensityModeller.findOverlaps(20)
        self.verticalLayout.removeWidget(self.tabWidget)
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.fillUi()


    def dumb(self):
        print('not yet implemented')

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
            filename = self.settings['spectralData'][0:-4] + '_out' + '.xlsx'
        elif filename[-4:]!= 'xlsx':
            filename += 'xlsx'
        output = os.path.join(outputPath, filename)
        excelWriter = ExcelWriter(output, self.configs)
        self._analyser.listOfIons = list(self.intensityModeller.getObservedIons().values())
        excelWriter.toExcel(self._analyser, self.intensityModeller, self.settings,
                self.libraryBuilder.getSequence().getSequenceList(), self.libraryBuilder.getFragmentLibrary(),
                            self.spectrumHandler.searchedChargeStates)
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