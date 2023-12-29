'''
Created on 21 Jul 2020

@author: michael
'''
import os
from abc import ABC

import numpy as np
import pandas as pd
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt

from src.BACHEM_extension.services.TD_Assigner import peakDtype, snapDtype
from src.gui.GUI_functions import setIcon, translate
from src.gui.widgets.Widgets import ShowFormulaWidget
from src.repositories.SpectralDataReader import SpectralDataReader
from src.resources import path, DEVELOP
from src.gui.controller.IsotopePatternView import AddIonView
from src.gui.dialogs.CalibrationView import CalibrationView
from src.gui.tableviews.TableViews import TableView
from src.gui.widgets.InfoView import InfoView
from src.gui.tableviews.TableModels import IonTableModel
from src.gui.tableviews.ShowPeaksViews import PeakView, SimplePeakView
from src.gui.widgets.SpectrumView import SpectrumView


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
            reader = SpectralDataReader()
            self._calibrator.calibratePeaks(self._spectrumHandler.getSpectrum())
            peaks = self.calibrateAndWrite(reader.openFile(self._settings['spectralData'], peakDtype),
                                           self._settings['spectralData'], reader)
            self._spectrumHandler.setSpectrum(peaks)
            self.calibrateAndWrite(reader.openFile(self._settings['calIons'], snapDtype), self._settings['calIons'],
                                   reader)
            if 'profile' in self._settings.keys() and self._settings['profile'] != "":
                profile = self.calibrateAndWrite(self._spectrumHandler.getProfileSpectrum(), self._settings['profile'], reader)
                self._spectrumHandler.setProfileSpectrum(profile)
            vals = self._calibrator.getCalibrationValues()
            self._info.calibrate(vals[0], vals[1], self._calibrator.getQuality(), self._calibrator.getUsedIons())
            return True
        else:
            return False
        """dlg = CalibrationView(self._calibrator)
        dlg.exec_()
        if dlg and not dlg.canceled():
            print('calibrating')
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
            return False"""

    def calibrateAndWrite(self, data, fileName, reader):
        calibrated = self._calibrator.calibratePeaks(data)
        """if not self._configs['overwrite']:
            fileName = fileName[:-4] + '_cal' + ".txt"  # +peakFileName[-4:]"""
        reader.writeData(calibrated, self.getCalibratedFileName(fileName))
        return calibrated

    def getCalibratedFileName(self, oldName):
        if self._configs['overwrite']:
            return oldName
        else:
            index = -4
            if oldName.endswith("xy"):
                index = -3
            return oldName[:index] + '_cal' + ".txt"  # +peakFileName[-4:]

    def setUpUi(self):
        '''
        Opens a SimpleMainWindow with the ion lists and a InfoView with the protocol
        '''
        self._openWindows = []
        #self._mainWindow = SimpleMainWindow(None, 'Results:  ' + os.path.split(self._settings['spectralData'])[-1])
        self._translate = translate
        self._mainWindow.setWindowTitle(self._translate(self._mainWindow.objectName(),
                                                        'Results:  ' + os.path.split(self._settings['spectralData'])[-1]))
        self._openWindows.append(self._mainWindow)
        self._centralwidget = self._mainWindow.centralWidget()
        self.verticalLayout = QtWidgets.QVBoxLayout(self._centralwidget)
        self._tabWidget = QtWidgets.QTabWidget(self._centralwidget)
        self._infoView = InfoView(None, self._info)
        self._openWindows.append(self._infoView)
        self.createMenuBar()
        self._mainWindow.makeHelpMenu()
        self.fillMainWindow()
        self._mainWindow.resize(1000, 900)
        self._mainWindow.show()


    def makeGeneralOptions(self):
        actionDict = dict()
        editActions = {'Repeat Ovl. Modelling':
                           (self.repeatModellingOverlaps, 'Repeat overlap modelling involving user inputs', None),
                            'Add New Ion':(self.addNewIonView, 'Add an ion manually', None),}
        # 'Take Shot':(self.shootPic,'', None),}
        if DEVELOP:
            editActions['Take shot'] = (self.shootPic, '', None)
        _, actions = self._mainWindow.createMenu("Edit", editActions, None)
        actionDict.update(actions)
        _, actions = self._mainWindow.createMenu("Show",
                                                 {'Results': (
                                                 self._mainWindow.show, 'Shows lists of observed and deleted ions',
                                                 None),
                                                  'Original Values': (
                                                  self.showRemodelledIons, 'Shows original values of overlapping ions',
                                                  None),
                                                  'Protocol': (self._infoView.show, 'Shows protocol', None),
                                                 'Spectrum': (self.showAllInSpectrum, 'Shows the entire spectrum', None),
                                                 'Ion Evaluation View': (self.makeEvaluationView, 'Displays the '
                                                                                                  'currently selected ion', None)},
                                                 None)
        actionDict.update(actions)
        return actionDict

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
        table = TableView(parent, tableModel, fun, 3)
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
            #global spectrumView
            """ajacentIons, minLimit, maxLimit  = self._intensityModeller.getAdjacentIons(selectedHash)
            #minWindow, maxWindow, maxY = self._intensityModeller.getLimits(ajacentIons)
            peaks = self._spectrumHandler.getSpectrum(minLimit - 1, maxLimit + 1)
            minMz,maxMz = np.min(selectedIon.getIsotopePattern()['m/z']), np.max(selectedIon.getIsotopePattern()['m/z'])
            spectrumView = SpectrumView(None, peaks, ajacentIons, minMz,
                                        maxMz, np.max(selectedIon.getIsotopePattern()['I']),
                                        self._spectrumHandler.getSprayMode(),
                                        self._spectrumHandler.getNoise((np.min(peaks['m/z']),np.max(peaks['m/z']))),
                                        selectedHash)"""

            self._openWindows.append(self.getSpectrumView(None, selectedHash))
        elif action == peakAction:
            #global peakview
            peakView = PeakView(self._mainWindow, selectedIon, self._intensityModeller.remodelSingleIon, self.saveSingleIon)
            self._openWindows.append(peakView)
        elif action == formulaAction:
            self._openWindows.append(ShowFormulaWidget(selectedIon))
            """dlg = QtWidgets.QWidget(None)
            dlg.setWindowTitle(selectedIon.getName())
            # self.setWindowTitle(ion.getName())
            layout = QtWidgets.QVBoxLayout(dlg)
            label = QtWidgets.QLabel(selectedIon.getFormula().toString())
            label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            layout.addWidget(label)
            dlg.show()"""
        elif action == copyRowAction:
            df=pd.DataFrame(data=[table.model().getRow(selectedRow)], columns=table.model().getHeaders())
            df.to_clipboard(index=False,header=True)
        elif action == copyTableAction:
            df=pd.DataFrame(data=table.model().getData(), columns=table.model().getHeaders())
            df.to_clipboard(index=False,header=True)
        elif action == delAction:
            choice = QtWidgets.QMessageBox.question(self._mainWindow, "",
                                        actionStrings[mode] +' ' + selectedIon.getName() +"?",
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


    def getSpectrumView(self, parent, selectedHash, empty=False, view=None, strongFocus=False):
        """profileMode = False
        if 'profile' in self._settings.keys() and self._settings['profile'] == "":
            profileMode=True"""
        if empty: #nothing selected yet (start)
            return SpectrumView(parent, self._spectrumHandler.getSpectrum(), [], 0, 0, 0,
                                self._spectrumHandler.getSprayMode())
        if selectedHash is None: #Full spec
            ajacentIons = sorted(self.getIonList(), key=lambda obj: obj.getIsotopePattern()['m/z'][0])
            peaks = self._spectrumHandler.getSpectrum()
            minMz_focus, maxMz_focus, maxI = np.min(peaks['m/z']), np.max(peaks['m/z']), np.max(peaks['I'])
            minMz_total, maxMz_total = minMz_focus, maxMz_focus
            noise = self._spectrumHandler.getNoise()
            # minWindow, maxWindow, maxY = self._intensityModeller.getLimits(ajacentIons)
            peaks = self._spectrumHandler.getSpectrum()
            selectedHash = False
        else:
            if strongFocus:
                ajacentIons, minMz_total, maxMz_total = self._intensityModeller.getAdjacentIons(selectedHash,5)
            else:
                ajacentIons, minMz_total, maxMz_total = self._intensityModeller.getAdjacentIons(selectedHash)
            # minWindow, maxWindow, maxY = self._intensityModeller.getLimits(ajacentIons)
            minMz_total -= 2
            maxMz_total += 2
            peaks = self._spectrumHandler.getSpectrum(minMz_total, maxMz_total)
            selectedIon = self._intensityModeller.getIon(selectedHash)
            #broadenWindow = 0.2
            minMz_focus = min(selectedIon.getIsotopePattern()['m/z'])#-broadenWindow
            maxMz_focus = max(selectedIon.getIsotopePattern()['m/z'])#+broadenWindow
            """else:
                minMz = np.min(selectedIon.getIsotopePattern()['m/z'])
                maxMz = np.max(selectedIon.getIsotopePattern()['m/z'])"""
            maxI = np.max(selectedIon.getIsotopePattern()['I'])
            noise = self._spectrumHandler.getNoise((minMz_total, maxMz_total))
        profileSpec = None
        if 'profile' in self._settings.keys() and self._settings['profile'] != "":
            profileSpec = self._spectrumHandler.getProfileSpectrum((minMz_total, maxMz_total))
        if view is None:
            return SpectrumView(parent, peaks, ajacentIons, minMz_focus, maxMz_focus, maxI, self._spectrumHandler.getSprayMode(),
                                noise, selectedHash,profileSpec)
        else:
            return view.updateView(peaks, ajacentIons, minMz_focus, maxMz_focus, maxI, noise,selectedHash, profileSpec)

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
                                ''.join(self._propStorage.getSequenceList()), self._settings['sequName'],
                                self._settings['charge'], self._settings['fragmentation'],
                                self._settings['modifications'], self.addNewIon)
        self._openWindows.append(addIonView)

    def addNewIon(self, addIonView):
        '''
        Adds a new ion to the table
        '''
        newIon = addIonView.getIon()
        newIon.setCharge(abs(newIon.getCharge()))
        mz = newIon.getMonoisotopic()
        spectrum = self._spectrumHandler.getSpectrum()['m/z']
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
        remView = QtWidgets.QWidget(None)
        #title = 'Original Values of Overlapping Ions'
        #remView._translate = translate
        remView.setWindowTitle(self._translate(remView.objectName(), 'Original Values of Overlapping Ions'))
        ions = self._intensityModeller.getRemodelledIons()
        verticalLayout = QtWidgets.QVBoxLayout(remView)
        scrollArea, table = self.makeScrollArea(remView, [ion.getMoreValues() for ion in ions], self.showRedOptions)
        #table.customContextMenuRequested['QPoint'].connect(partial(self.showRedOptions, table))
        verticalLayout.addWidget(scrollArea)
        remView.resize(1000, 750)
        self._openWindows.append(remView)
        setIcon(remView)
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
            """global view
            ajacentIons, minLimit, maxLimit  = self._intensityModeller.getAdjacentIons(selectedHash)
            ajacentIons = [ion for ion in ajacentIons if ion.getHash()!=selectedHash]
            peaks = self._spectrumHandler.getSpectrum(minLimit - 1, maxLimit + 1)
            minMz,maxMz = np.min(selectedIon.getIsotopePattern()['m/z']), np.max(selectedIon.getIsotopePattern()['m/z'])
            view = SpectrumView(None, peaks, [selectedIon]+ajacentIons, minMz,maxMz,
                                np.max(selectedIon.getIsotopePattern()['I']), self._spectrumHandler.getSprayMode(),
                                (np.min(peaks['m/z']),np.max(peaks['m/z'])),selectedHash)"""
            self._openWindows.append(self.getSpectrumView(None, selectedHash))
        elif action == peakAction:
            global peakview
            peakview = SimplePeakView(None, selectedIon)
            self._openWindows.append(peakview)
        elif action == formulaAction:
            dlg = QtWidgets.QWidget(self._mainWindow)
            dlg.setWindowTitle(selectedIon.getName())
            # self.setWindowTitle(ion.getName())
            layout = QtWidgets.QVBoxLayout(dlg)
            label = QtWidgets.QLabel(selectedIon.getFormula().toString())
            label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            layout.addWidget(label)
            dlg.show()
        elif action == copyRowAction:
            df=pd.DataFrame(data=[table.model().getRow(selectedRow)], columns=table.model().getHeaders())
            df.to_clipboard(index=False,header=True)
        elif action == copyTableAction:
            df=pd.DataFrame(data=table.model().getData(), columns=table.model().getHeaders())
            df.to_clipboard(index=False,header=True)

    def getIonList(self):
        return list(self._intensityModeller.getObservedIons().values())

    def showAllInSpectrum(self):
        """global spectrumView
        ions = sorted(self.getIonList(),key=lambda obj:obj.getIsotopePattern()['m/z'][0])
        # minWindow, maxWindow, maxY = self._intensityModeller.getLimits(ajacentIons)
        peaks = self._spectrumHandler.getSpectrum()
        spectrumView = SpectrumView(None, peaks, ions, np.min(peaks['m/z']),np.max(peaks['m/z']),np.max(peaks['I']),
                                    self._spectrumHandler.getSprayMode(), self._spectrumHandler.getNoise())"""
        self._openWindows.append(self.getSpectrumView(None, None))
        if DEVELOP:
            for vals in self._spectrumHandler.getNoise():
                print(vals[0], vals[1])


    def makeEvaluationView(self):
        self._evaluationView = self.getSpectrumView(None, None, empty=True)
        #SpectrumView(None, self._spectrumHandler.getSpectrum(), [],0,0,0,self._spectrumHandler.getSprayMode())
        self._openWindows.append(self._evaluationView)
        #self._tables[0].clicked.connect(self.connectTableToView)
        self._tables[0].selectionModel().currentChanged.connect(self.connectTableToView)
        self._evaluationView.show()
        #self._tables[1].clicked.connect(self.connectTableToView)

    def connectTableToView(self, item):
        self.viewIsotopePeaks(None, self._tables[0], item.row(), self._evaluationView)

    def viewIsotopePeaks(self, parent, table, selectedRow, view=None):
        selectedHash = table.model().getHashOfRow(selectedRow)
        if selectedHash[0] == "":
            if view is None:
                return self.getSpectrumView(parent, None, True)
                #return SpectrumView(widget, self._spectrumHandler.getSpectrum(), [],0,0,0,self._spectrumHandler.getSprayMode())
            else:
                return view
        return self.getSpectrumView(parent, selectedHash,empty=False, view=view,strongFocus=True)
        """selectedIon = self._intensityModeller.getIon(selectedHash)
        ajacentIons, minLimit, maxLimit  = self._intensityModeller.getAdjacentIons(selectedHash,5)
        #minWindow, maxWindow, maxY = self._intensityModeller.getLimits(ajacentIons)
        peaks = self._spectrumHandler.getSpectrum(minLimit, maxLimit)
        broadenWindow = 0.2
        if view is None:
            spectrumView = SpectrumView(widget, peaks, ajacentIons, min(selectedIon.getIsotopePattern()['m/z'])-broadenWindow,
                                max(selectedIon.getIsotopePattern()['m/z'])+broadenWindow,
                                        max(selectedIon.getIsotopePattern()['I']),
                                        self._spectrumHandler.getSprayMode(),
                                        self._spectrumHandler.getNoise((min(peaks['m/z']),max(peaks['m/z']))),
                                        selectedHash)
            #spectrumView.setMaximumWidth(50)
            #spectrumView.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
            return spectrumView
        else:
            return view.updateView(peaks, ajacentIons, min(selectedIon.getIsotopePattern()['m/z'])-broadenWindow,
                                   max(selectedIon.getIsotopePattern()['m/z'])+broadenWindow,
                                   max(selectedIon.getIsotopePattern()['I']),
                                   self._spectrumHandler.getNoise((min(peaks['m/z']),max(peaks['m/z']))),
                                   selectedHash)"""