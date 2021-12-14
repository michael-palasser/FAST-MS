from math import log10
import pandas as pd

from PyQt5 import QtWidgets, QtCore

from src.Exceptions import InvalidInputException
from src.gui.GUI_functions import connectTable, showOptions


class GeneralPeakWidget(QtWidgets.QTableWidget):
    '''
    QTableWidget which shows peak values. Parent class of IsoPatternPeakWidget and PeakWidget.
    Spectral intensity column is interactive.
    '''
    def __init__(self, parent, headers, format, peaks):
        super(GeneralPeakWidget, self).__init__(parent)
        self._headers = headers
        self._format = format
        self._peaks = peaks
        self.setWindowTitle('')
        self.setColumnCount(len(self._headers))
        self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.setRowCount(len(self._peaks))
        self.fill()
        self.setHorizontalHeaderLabels(self._headers)
        self.setSortingEnabled(True)
        #connectTable(self, self.showOptions)

        '''self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested['QPoint'].connect(partial(self.showOptions, self))'''


    def fill(self):
        '''
        Fills the table with the peak data
        '''
        #print(self.getValue(ion))
        for row, peak in enumerate(self._peaks):
            for j, item in enumerate(peak):
                newItem = QtWidgets.QTableWidgetItem()
                newItem.setTextAlignment(QtCore.Qt.AlignRight)
                if j == 1 or j==2:
                    formatString = self._format[2]
                    item = int(round(item))
                    if item >= 10 ** 12:
                        lg10 = str(int(log10(item) + 1))
                        formatString = '{:' + lg10 + 'd}'
                    newItem.setData(QtCore.Qt.DisplayRole, formatString.format(item))
                    if j==2:
                        newItem.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                elif j==len(peak)-1:
                    newItem = QtWidgets.QTableWidgetItem()
                    if item:
                        newItem.setCheckState(QtCore.Qt.Checked)
                    else:
                        newItem.setCheckState(QtCore.Qt.Unchecked)
                else:
                    newItem.setData(QtCore.Qt.DisplayRole, self._format[j].format(item))
                    newItem.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                self.setItem(row, j, newItem)
        #self.resizeColumnsToContents()
        self.resizeRowsToContents()
        self.resizeColumnsToContents()



    """def showOptions(self, table, pos):
        '''
        Right click options of the table
        '''
        menu = QtWidgets.QMenu()
        copyAllAction = menu.addAction("Copy Table")
        copyAction = menu.addAction("Copy Cell")
        action = menu.exec_(table.viewport().mapToGlobal(pos))
        if action == copyAllAction:
            df = self.getDataframe()
            df.to_clipboard(index=False,header=True)
        if action == copyAction:
            it = table.indexAt(pos)
            if it is None:
                return
            selectedRow = it.row()
            selectedCol = it.column()
            df = pd.DataFrame([self._peaks[selectedRow][selectedCol]])
            df.to_clipboard(index=False, header=False)

    def getDataframe(self):
        '''
        Returns a dataframe with the peak data
        '''
        df = pd.DataFrame()#data=self._peaks), columns=self._headers)
        df['m/z'] = self._peaks['m/z']
        df['int. (spectrum)'] = self._peaks['relAb']
        df['int. (calc.)'] = self._peaks['calcInt']
        df['error /ppm'] = self._peaks['error']
        df['used'] = self._peaks['used']
        return df"""

    def readTable(self):
        itemList = []
        for row in range(self.rowCount()):
            itemList.append((int(self.item(row, 1).text()), int(self.item(row, 4).checkState()/2)==1))
        return itemList

    def setPeaks(self, peaks):
        self._peaks = peaks
        self.fill()

    def getPeaks(self):
        return self._peaks


class PeakWidget(GeneralPeakWidget):
    '''
    QTableWidget which shows peak values. Used by PeakView (in top-down search)
    '''
    def __init__(self, parent, peaks):
        super(PeakWidget, self).__init__(parent, ('m/z','int. (spectrum)','int. (calc.)','error /ppm', 'used'),
                                         ('{:10.5f}','{:11d}', '{:11d}', '{:4.2f}', ''), peaks)
        connectTable(self, showOptions)


    def getData(self):
        data = []
        for row in range(self.rowCount()):
            try:
                intensity = 0
                if self.item(row, 1).text() != '':
                    intensity = int(self.item(row, 1).text())
                data.append((self.item(row, 0).text(), intensity, self.item(row, 2).text(), self.item(row, 3).text(),
                             int(self.item(row, 4).checkState()/2)==1))
            except ValueError:
                raise InvalidInputException('Intensities must be numbers', 'Incorrect entry: '+self.item(row, 1).text())
        return data


class IsoPatternPeakWidget(GeneralPeakWidget):
    '''
    QTableWidget which shows peak values. Used by IsotopePatternView (for isotope pattern tool)
    '''
    def __init__(self, parent, peaks):
        super(IsoPatternPeakWidget, self).__init__(parent, ('m/z','int. (spectrum)','int. (calc.)', 'used'),
                                         ('{:10.5f}','{:11d}', '{:11d}', ''), peaks)
        connectTable(self, self.showOptions)


    '''def readTable(self):
        itemList = []
        for row in range(self.rowCount()):
            try:
                intensity = 0
                if self.item(row, 1).text() != '':
                    intensity = int(self.item(row, 1).text())
                itemList.append((intensity, int(self.item(row, 3).checkState()/2)==1, float(self.item(row, 0).text()),
                                 ))
            except ValueError:
                raise InvalidInputException('Intensities must be numbers', 'Incorrect entry: '+self.item(row, 1).text())
        return itemList'''

    def getData(self):
        data = []
        for row in range(self.rowCount()):
            try:
                intensity = 0
                if self.item(row, 1).text() != '':
                    intensity = int(self.item(row, 1).text())
                data.append((self.item(row, 0).text(), intensity, self.item(row, 2).text(),
                             int(self.item(row, 3).checkState()/2)==1))
            except ValueError:
                raise InvalidInputException('Intensities must be numbers', 'Incorrect entry: '+self.item(row, 1).text())
        return data

    """def getDataframe(self):
        '''
        Returns a dataframe with the peak data
        '''
        '''df = pd.DataFrame(data=self._peaks, columns=self._headers)
        df['int. (spectrum)'] = self._peaks['relAb']
        df['int. (calc.)'] = self._peaks['calcInt']'''
        df = pd.DataFrame()#data=self._peaks), columns=self._headers)
        df['m/z'] = self._peaks['m/z']
        df['int. (spectrum)'] = self._peaks['relAb']
        df['int. (calc.)'] = self._peaks['calcInt']
        df['used'] = self._peaks['used']
        return df"""


    def updateTable(self, newPeaks):
        self._peaks = newPeaks
        rowCount = self.rowCount()
        nrRows = len(self._peaks)-rowCount
        if nrRows>0:
            [self.insertRow(rowCount+i) for i in range(nrRows)]
        elif nrRows<0:
            [self.removeRow(rowCount-i-1) for i in range(abs(nrRows))]
        self.fill()

    def showOptions(self, table, pos):
        '''
        Right click options of the table
        '''
        menu = QtWidgets.QMenu()
        copyAllAction = menu.addAction("Copy Table")
        copyAction = menu.addAction("Copy Cell")
        deleteAction = menu.addAction("Delete last Peak")
        action = menu.exec_(table.viewport().mapToGlobal(pos))
        if action == copyAllAction:
            #df = self.getDataframe()
            df = pd.DataFrame(self.getData(), columns=self._headers)
            df.to_clipboard(index=False, header=True)
        if action == copyAction:
            it = table.indexAt(pos)
            if it is None:
                return
            selectedRow = it.row()
            selectedCol = it.column()
            #df = pd.DataFrame([self._peaks[selectedRow][selectedCol]])
            df = pd.DataFrame([self.getData()[selectedRow][selectedCol]])
            df.to_clipboard(index=False, header=False)
        if action == deleteAction:
            print(self._peaks[-1])
            self.updateTable(self._peaks[:-1])