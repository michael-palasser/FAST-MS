'''
Created on 21 Jul 2020

@author: michael
'''



from copy import deepcopy
from datetime import datetime
import os

from numpy import sort
import pandas as pd
from PyQt5 import QtWidgets
from src.BACHEM_extension.gui.Dialog_MD import MD_ScoreParameterDialog, MDStartDialog
from src.BACHEM_extension.gui.MD_Tables import MD_BestIonsTableModel
from src.BACHEM_extension.services.MDEvaluationWriter import MDEvaluationWriter
from src.BACHEM_extension.services.MD_analyser import MD_Analyser
from src.BACHEM_extension.services.PeakMatcher import PeakMatcher
from src.gui.AbstractMainWindows import SimpleMainWindow
from src.gui.GUI_functions import getData, showOptions
from src.gui.controller.AbstractController import AbstractMainController
from src.gui.dialogs.CalibrationView import CalibrationView
from src.gui.tableviews.TableModels import AbstractTableModel
from src.gui.tableviews.TableViews import TableView
from src.repositories.SpectralDataReader import SpectralDataReader
from src.gui.controller.TD_searchController import TD_MainController
from src.BACHEM_extension.services.TD_Assigner import snapDtype, makeArray,peakDtype
from src.resources import path, autoStart
from src.services.assign_services.AbstractSpectrumHandler import getMz
from src.services.assign_services.Finders import TD_Finder

"""def sortIonsByName(ionList):
    #return sorted(ionList,key=lambda obj:(obj.type ,obj.number))
    return sorted(ionList, key=lambda obj: (obj.getName(), obj.getCharge()))"""



#if __name__ == '__main__':
class MD_MainController(TD_MainController):
    '''
    Controller class for starting, saving, exporting and loading a spectrum for MS/MS method development
    '''

    def search(self):
        self._settings['fragLib'] = ''
        self._settings['noiseLimit'] = 0
        if self._settings['calibration']:
            self._settings['calIons']=self._settings['snapData']
        super(MD_MainController, self).search()
        reader = SpectralDataReader()
        ionData = reader.openFile(self._settings['snapData'], snapDtype)
        print("\n********** Search through SNAP list **********")
        allSettings = deepcopy(self._configs)
        allSettings.update(self._settings)
        finder = TD_Finder(self._libraryBuilder.getFragmentLibrary(), allSettings, self._spectrumHandler.getChargeRange)
        assignedIons = finder.findIonsInSpectrum(self._configs['k'], self._configs['d'], ionData)
        print("done")
        print("\n********** Matching with Peak Data **********")
        peakData = reader.openFile(self._settings['spectralData'], peakDtype)
        peakMatcher = PeakMatcher(self._configs['k'], self._configs['d'], peakDtype)
        self._assignedIons, overlapList = peakMatcher.matchPeaks(assignedIons, peakData)
        allIons = list(self._intensityModeller.getObservedIons().values())+list(self._intensityModeller.getDeletedIons().values())
        self._matchedIons = peakMatcher.matchIons(allIons, self._assignedIons)
        
        self._matchedPeaks = peakMatcher.matchPeaks2(allIons, peakData)
        self._foundPeakList = self._spectrumHandler.findMonoisotopics(self._libraryBuilder.getFragmentLibrary(),peakData)
        self._analyserMD = MD_Analyser(len(self._propStorage.getSequenceList()))

        precursorMass = sort(self._libraryBuilder.getPrecursor().getIsotopePattern(),order = 'calcInt')[-1]['m/z']
        self._precursorMz = abs(getMz(precursorMass,self._settings['charge'],0))
        print("done")
        #self.analyseData()
        return 0


    @staticmethod
    def startDialog(parent):
        return MDStartDialog(parent)

    def createMenuBar(self):
        '''
        Makes the QMenuBar
        :return:
        '''
        self._mainWindow.createMenuBar()
        self._actions = dict()
        _,actions = self._mainWindow.createMenu("File", {'Export': (self.export,'Exports the results to Excel',None),
                                                         'Close': (self.close,None,"Ctrl+Q")}, None)
        self._actions.update(actions)
        self._actions.update(self.makeGeneralOptions())
        _,actions = self._mainWindow.createMenu("Analysis",
                {'Best Ions': (self.showBest, 'Show fragmentation efficiencies (% of each fragment type)', None),
                 'Occupancies': (self.showOccupancyPlot,'Show occupancies as a function of sequence pos.',None),
                 'Fragmentation': (self.showFragmentation, 'Show fragmentation efficiencies (% of each fragment type)', None),
                 'Charge States': (lambda: self.showChargeDistrPlot(False),'Show av. charge as a function of cleavage site (Calculated with int. values)',None),
                 'Sequence Coverage': (self.showSequenceCoverage,'Show sequence coverage',None)}, None)
        self._actions.update(actions)



    def calibrate(self):
        dlg = CalibrationView(self._calibrator)
        dlg.exec_()
        if dlg and not dlg.canceled():
            reader = SpectralDataReader()
            calibratedPeaks = self._calibrator.calibratePeaks(reader.openFile(self._settings['spectralData'], peakDtype))
            self._calibrator.calibratePeaks(self._spectrumHandler.getSpectrum())
            calibratedIons = self._calibrator.calibratePeaks(reader.openFile(self._settings['snapData'], snapDtype))
            peakFileName = self._settings['spectralData']
            snapFileName = self._settings['snapData']
            if not self._configs['overwrite']:
                peakFileName = peakFileName[:-4]+'_cal'+".txt"#+peakFileName[-4:]
                snapFileName = snapFileName[:-4]+'_cal'+".txt"#+snapFileName[-4:]
                self._settings['spectralData'] = peakFileName
                self._settings['snapData'] = snapFileName
            reader.writeData(calibratedPeaks, peakFileName)
            reader.writeData(calibratedIons, snapFileName)
            vals = self._calibrator.getCalibrationValues()
            self._info.calibrate(vals[0], vals[1], self._calibrator.getQuality(), self._calibrator.getUsedIons())
            return True
        else:
            return False

    def makeTable(self, parent, data,fun):
        '''
        Makes an ion table
        '''
        return AbstractMainController.makeTable(self, parent, data,fun, (self._precursorMz-5,self._precursorMz+5))

        
    def showBest(self):
        self._sortedLibrary, self._best = self._analyserMD.sortIons(self._intensityModeller.getObservedIons(), self._matchedIons, self._matchedPeaks, self._precursorMz)
        precursorRegion = (self._precursorMz-5,self._precursorMz+5)
        self._analysisTables, self._analysisSpectra = [], []

        analysisWindow = SimpleMainWindow(None,"MS/MS MD Analysis")
        centralWidget = analysisWindow.centralWidget()
        #analysisWindow = QtWidgets.QWidget(None)
        self._openWindows.append(analysisWindow)
        analysisLayout = QtWidgets.QVBoxLayout(centralWidget)

        evaluationWidget = QtWidgets.QWidget(centralWidget)
        analysisLayout.addWidget(evaluationWidget,1)

        bestWidget = self.showAnalysisTable(centralWidget, self._best, precursorRegion)
        analysisLayout.addWidget(bestWidget,10)

        alternativeWidget = self.showAnalysisTable(centralWidget, self._sortedLibrary[0], precursorRegion, self.showMoreOptions)
        analysisLayout.addWidget(alternativeWidget,6)
        
        self._analysisTables.append(self.makeEvaluationTable(evaluationWidget))

        #self._analysisTables[0].clicked.connect(self.connectBestTable)
        self._analysisTables[0].selectionModel().currentChanged.connect(self.connectBestTable)
        #self._analysisTables[1].clicked.connect(self.connectAlternativeTable)
        self._analysisTables[1].selectionModel().currentChanged.connect(self.connectAlternativeTable)
        analysisWindow.createMenuBar()
        analysisWindow.createMenu("File", {'Settings': (self.showScoreSettings,'Edit the reward and penalty values for calculating the score',None),
                                           'Export': (self.exportMD,'Exports the analysis to Excel',None)}, 
                                           None)
        #ToDo: Change Parameters, 
        analysisWindow.resize(1200, 750)
        analysisWindow.show()

    def makeEvaluationTable(self,evaluationWidget):
        evaluation = self._analyserMD.evaluate(self._analysisTables[0].model().getSNs())
        tableModel = AbstractTableModel((evaluation,), ('{:6.1f}', '{:6.1f}','{:6.1f}'), ('Minimum','1. Quartile','Median'))
        evaluationLayout = QtWidgets.QHBoxLayout(evaluationWidget)
        table = TableView(evaluationWidget, tableModel)
        table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        table.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        table.resizeRowsToContents()
        table.resizeColumnsToContents()
        evaluationLayout.addWidget(table)
        return table

    def showAnalysisTable(self, widget, data, precursorRegion, fun = showOptions):
        curWidget = QtWidgets.QWidget(widget)
        curLayout = QtWidgets.QHBoxLayout(curWidget)

        scrollArea = QtWidgets.QScrollArea(curWidget)
        scrollArea.setWidgetResizable(True)
        tableModel = MD_BestIonsTableModel(data, precursorRegion)
        table = TableView(curWidget, tableModel, optionFun=fun, sort=0)
        table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        table.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        table.resizeRowsToContents()

        table.horizontalHeader().setMaximumSectionSize(2000)
        table.resizeColumnsToContents()
        scrollArea.setWidget(table)
        curLayout.addWidget(scrollArea,5)
        self._analysisTables.append(table)

        spectrum = self.viewIsotopePeaks(curWidget, table, 0, None)
        curLayout.addWidget(spectrum,2)
        self._analysisSpectra.append(spectrum)
        return curWidget
    
    """def viewIsotopePeaks(self, widget, table, selectedRow, view = None):
        selectedHash = table.model().getHashOfRow(selectedRow)

        if selectedHash[0] == "":
            if view == None:
                return SpectrumView(widget, self._spectrumHandler.getSpectrum(), [],0,0,0,
                                    self._spectrumHandler.getSprayMode())
            else: 
                return view
        selectedIon = self._intensityModeller.getIon(selectedHash)
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


    def connectBestTable(self, item):        
        self._analysisTables[1].model().setData(self._sortedLibrary[getData(self._analysisTables[0])[0][item.row()][0]-1])
        self.viewIsotopePeaks(None, self._analysisTables[0], item.row(), self._analysisSpectra[0])
        self.viewIsotopePeaks(None, self._analysisTables[1], 0, self._analysisSpectra[1])
        self._analysisTables[2].model().setData((self._analyserMD.evaluate(self._analysisTables[0].model().getSNs()),))
        #self._analysisSpectra[0]
        
    def connectAlternativeTable(self, item):
        self.viewIsotopePeaks(None, self._analysisTables[1], item.row(), self._analysisSpectra[1])


    def showMoreOptions(self, table, pos):
        menu = QtWidgets.QMenu()
        selectAction = menu.addAction("Select Ion")
        copyAllAction = menu.addAction("Copy Table")
        copyAction = menu.addAction("Copy Cell")
        action = menu.exec_(table.viewport().mapToGlobal(pos))
        data, headers = getData(table)
        if action == selectAction:
            it = table.indexAt(pos)
            if it is None:
                return
            #data = getData(self._analysisTables[0])[0][selectedRow]
            self._analysisTables[0].model().updateData(data[it.row()])
            self._analysisTables[0].show()
            #df = pd.DataFrame(data=[table.model().getData()[selectedRow][selectedCol]])
        if action == copyAction:
            it = table.indexAt(pos)
            if it is None:
                return
            selectedRow = it.row()
            selectedCol = it.column()
            #df = pd.DataFrame(data=[table.model().getData()[selectedRow][selectedCol]])
            df = pd.DataFrame(data=[data[selectedRow][selectedCol]])
            df.to_clipboard(index=False, header=False)
        elif action == copyAllAction:
            df = pd.DataFrame(data=data, columns=headers)
            df.to_clipboard(index=False, header=True)

    def showScoreSettings(self):
        dialog = MD_ScoreParameterDialog()
        dialog.exec_()
        if dialog.canceled():
            return

    def exportMD(self):
        '''
        Exports the MS/MS MD analysis to a xlsx file
        '''
        #ToDo: Dlg
        writer = MDEvaluationWriter(self._precursorMz)
        #try:
        #formatedIons = [formatVals(ion, (-5, -4)) for ion in ionArray]
        output = self._settings["output"]
        if output == '':
            output =  self._settings['spectralData'][:-4] + "_MD_" + datetime.now().strftime("%d.%m.%Y") + ".xlsx"
        else:
            output =  os.path.join(path,'Spectral_data', output  + ".xlsx")
        allSettings = self._settings
        allSettings.update(self._configs)
        allSettings.update(self._analyserMD.getScoreDict())
        bestTable = self._analysisTables[0]
        formulaLib = {ion.getName(): ion.getFormula().toString() for ion in self._intensityModeller.getObservedIons().values()}
        writer.makeOutput(output, allSettings, list(bestTable.model().getHeaders())+["formula"], self._sortedLibrary, 
                          getData(bestTable)[0],formulaLib, self._propStorage.getSequenceList(), 
                          makeArray(self._assignedIons),self._foundPeakList, self._info.toString())
        autoStart(output)

