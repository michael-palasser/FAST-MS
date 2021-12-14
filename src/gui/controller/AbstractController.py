'''
Created on 21 Jul 2020

@author: michael
'''
import os
from abc import ABC

import numpy as np
import pandas as pd
from PyQt5 import QtWidgets, QtCore

from src import path
from src.gui.IsotopePatternView import AddIonView
from src.gui.dialogs.CalibrationView import CalibrationView
from src.gui.tableviews.TableViews import TableView
from src.gui.widgets.InfoView import InfoView
from src.gui.tableviews.TableModels import IonTableModel
from src.gui.tableviews.ShowPeaksViews import PeakView, SimplePeakView
from src.gui.widgets.SpectrumView import SpectrumView

FOTO_SESSION=True


class AbstractMainController(ABC):
    '''
    Controller class for starting, saving, exporting and loading a top-down search/analysis
    '''
    def __init__(self, window):
        '''
        Starts either the search or loads a search from the database. Afterwards, result windows are shown.
        :param parent:
        :param (bool) new: True if new search, False if old search is loaded
        '''
        self._mainWindow= window


    def calibrate(self):
        dlg = CalibrationView(self._calibrator)
        dlg.exec_()
        if dlg and not dlg.canceled():
            peaks = self._calibrator.calibratePeaks(self._spectrumHandler.getSpectrum())
            fileName = self._settings['spectralData']
            if not self._configs['overwrite']:
                fileName = fileName[:-4]+'_cal'+fileName[-4:]
                self._settings['spectralData'] = fileName
            self._calibrator.writePeaks(peaks, fileName)
            vals = self._calibrator.getCalibrationValues()
            self._info.calibrate(vals[0], vals[1], self._calibrator.getQuality(), self._calibrator.getUsedIons())
            return True
        else:
            return False

    def setUpUi(self):
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
        self._mainWindow.show()


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

    def shootPic(self):
        widgets = {w.windowTitle():w for w in self._openWindows}
        item, ok = QtWidgets.QInputDialog.getItem(self._mainWindow, "Shoot",
                                        "Select the window", list(widgets.keys()), 0, False)
        if ok and item:
            p=widgets[item].grab()
            p.save(os.path.join(path,'pics',item+'.png'), 'png')
            print('Shoot taken')

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

    def makeTable(self, parent, data,fun, precursorRegion=None):
        '''
        Makes an ion table
        '''
        tableModel = IonTableModel(data, precursorRegion, self._configs['shapeMarked'], self._configs['scoreMarked'])
        table = TableView(parent, tableModel, fun)
        """table = QtWidgets.QTableView(parent)
        table.setModel(tableModel)
        table.setSortingEnabled(True)
        #table.setModel(self.proxyModel)
        '''table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        table.customContextMenuRequested['QPoint'].connect(partial(fun, table))'''
        connectTable(table, fun)
        #table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        table.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)"""
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
                table.model().removeByIndex(selectedRow)
                self._tables[other].model().addData(selectedIon.getMoreValues())
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


    def addNewIonView(self):
        '''
        Starts an AddIonView to create a new ion (which was not found by the main search)
        '''
        addIonView = AddIonView(self._mainWindow, self._propStorage.getMolecule().getName(),
                                ''.join(self._propStorage.getSequenceList()), self._settings['charge'],
                                self._settings['fragmentation'], self._settings['modifications'], self.addNewIon)
        self._openWindows.append(addIonView)

    def addNewIon(self, addIonView):
        '''
        Adds a new ion to the table
        '''
        newIon = addIonView.getIon()
        newIon.setCharge(abs(newIon.getCharge()))
        mz = newIon.getMonoisotopic()
        spectrum = self._spectrumHandler.getSpectrum()[:,0]
        if int(mz) not in range(int(np.min(spectrum)), int(np.max(spectrum))+1):
            newIon.setNoise(self._spectrumHandler.getNoiseLevel())
        else:
            newIon.setNoise(self._spectrumHandler.calculateNoise(mz, self._configs['noiseWindowSize']))

        oldIon = None
        index = -1
        hash = newIon.getHash()
        if hash in list(self._intensityModeller.getObservedIons().keys()) + list(self._intensityModeller.getDeletedIons().keys()):
            warning = newIon.getName() + ', ' + str(newIon.getCharge()) + ' is already in the list. \n' \
                                                                          'Should the old ion be overwritten?'
            choice = QtWidgets.QMessageBox.question(self._mainWindow, 'Warning',warning, QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if choice == QtWidgets.QMessageBox.No:
                return
            if hash in self._intensityModeller.getObservedIons().keys():
                oldIon = self._intensityModeller.getObservedIons()[hash]
                index = 0
            else:
                oldIon = self._intensityModeller.getDeletedIons()[hash]
                index = 1
        self._intensityModeller.addNewIon(newIon)
        if oldIon is None:
            self._tables[0].model().addData(newIon.getMoreValues())
        else:
            if index ==0:
                self._tables[0].model().updateData(newIon.getMoreValues())
            else:
                self._tables[1].model().removeData(newIon.getName(), newIon.getCharge())
                self._tables[0].model().addData(newIon.getMoreValues())
        self._info.addNewIon(newIon, oldIon)
        self._infoView.update()
        self._saved = False
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

    '''def dumb(self):
        print('not yet implemented')
        dlg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Information, 'Unvalid Request',
                    'Sorry, not implemented yet', QtWidgets.QMessageBox.Ok, self._mainWindow, )
        if dlg.exec_() and dlg == QtWidgets.QMessageBox.Ok:
            return'''

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
            for w in self._openWindows:
                #if w is not None:
                try:
                    w.close()
                except AttributeError:
                    pass
            self._mainWindow.close()
            self._infoView.close()

    def showRemodelledIons(self):
        '''
        Makes a table with the original values of the remodelled ions
        '''
        remView = QtWidgets.QWidget(self._mainWindow)
        #title = 'Original Values of Overlapping Ions'
        remView._translate = QtCore.QCoreApplication.translate
        remView.setWindowTitle(self._translate(remView.objectName(), 'Original Values of Overlapping Ions'))
        ions = self._intensityModeller.getRemodelledIons()
        verticalLayout = QtWidgets.QVBoxLayout(remView)
        scrollArea, table = self.makeScrollArea(remView, [ion.getMoreValues() for ion in ions], self.showRedOptions)
        #table.customContextMenuRequested['QPoint'].connect(partial(self.showRedOptions, table))
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

    def getIonList(self):
        return list(self._intensityModeller.getObservedIons().values())

