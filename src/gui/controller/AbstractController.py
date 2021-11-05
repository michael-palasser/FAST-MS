'''
Created on 21 Jul 2020

@author: michael
'''
import subprocess
import traceback
import os
from abc import ABC
from datetime import datetime

import numpy as np
import time
import pandas as pd
from PyQt5 import QtWidgets, QtCore

from src import path
from src.Exceptions import InvalidInputException
from src.Services import IntactIonService, SequenceService
from src.entities.Info import Info
from src.entities.IonTemplates import IntactModification
from src.gui.GUI_functions import connectTable
from src.gui.IsotopePatternView import AddIonView
from src.gui.widgets.InfoView import InfoView
from src.intact.IntactAnalyser import IntactAnalyser
from src.intact.IntactExcelWriter import IntactExcelWriter, FullIntactExcelWriter
from src.intact.IntactFinder import Calibrator
from src.intact.IntactLibraryBuilder import IntactLibraryBuilder
from src.intact.IntactSpectrumHandler import IntactSpectrumHandler
from src.repositories.ConfigurationHandler import ConfigurationHandlerFactory
from src.top_down.IntensityModeller import IntensityModeller
from src.gui.dialogs.CheckIonView import CheckMonoisotopicOverlapView
from src.gui.tableviews.TableModels import IonTableModel
from src.gui.tableviews.ShowPeaksViews import PeakView, SimplePeakView
from src.gui.dialogs.SimpleDialogs import ExportDialog
from src.gui.dialogs.StartDialogs import IntactStartDialogFull
from src.gui.widgets.SpectrumView import SpectrumView


FOTO_SESSION=True


class AbstractMainController(ABC):
    '''
    Controller class for starting, saving, exporting and loading a top-down search/analysis
    '''
    def __init__(self, parent, new, window):
        '''
        Starts either the search or loads a search from the database. Afterwards, result windows are shown.
        :param parent:
        :param (bool) new: True if new search, False if old search is loaded
        '''
        self._mainWindow= window
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
            self._calibrator = Calibrator(self._libraryBuilder.getNeutralLibrary(),self._settings)
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
        self._intensityModeller.remodelComplexPatterns(complexPatterns, [])
        self._info.searchFinished(self._spectrumHandler.getUpperBound())
        print("done")
        return 0

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

    def makeTable(self, parent, data,fun):
        '''
        Makes an ion table
        '''
        tableModel = IonTableModel(data, None, self._configs['shapeMarked'], self._configs['scoreMarked'])

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
        self.fillMainWindow()

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

    def getIonList(self):
        return list(self._intensityModeller.getObservedIons().values())

