from math import log10

from PySide6 import QtWidgets
from PySide6.QtCore import Qt

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
        self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.setRowCount(len(self._peaks))
        self.fill()
        self.setHorizontalHeaderLabels(self._headers)
        self.setSortingEnabled(True)


    def fill(self):
        '''
        Fills the table with the peak data
        '''
        for row, peak in enumerate(self._peaks):
            for j, item in enumerate(peak):
                newItem = QtWidgets.QTableWidgetItem()
                newItem.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                if j == 1 or j==2:
                    formatString = self._format[2]
                    item = int(round(item))
                    if item >= 10 ** 12:
                        lg10 = str(int(log10(item) + 1))
                        formatString = '{:' + lg10 + 'd}'
                    newItem.setData(Qt.ItemDataRole.DisplayRole, formatString.format(item))
                    if j==2:
                        newItem.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                elif j==len(peak)-1:
                    newItem = QtWidgets.QTableWidgetItem()
                    if item:
                        newItem.setCheckState(Qt.CheckState.Checked)
                    else:
                        newItem.setCheckState(Qt.CheckState.Unchecked)
                else:
                    newItem.setData(Qt.ItemDataRole.DisplayRole, self._format[j].format(item))
                    newItem.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                self.setItem(row, j, newItem)
        self.resizeRowsToContents()
        self.resizeColumnsToContents()

    def readTable(self):
        itemList = []
        for row in range(self.rowCount()):
            itemList.append((int(self.item(row, 1).text()), self.item(row, 4).checkState() == Qt.CheckState.Checked))
        return itemList

    def setPeaks(self, peaks):
        self._peaks = peaks
        self.fill()

    def getPeaks(self):
        return self._peaks

    def getHeaders(self):
        return self._headers


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
                             self.item(row, 4).checkState() == Qt.CheckState.Checked))
            except ValueError:
                raise InvalidInputException('Intensities must be numeric', 'Incorrect entry: '+self.item(row, 1).text())
        return data


class IsoPatternPeakWidget(GeneralPeakWidget):
    '''
    QTableWidget which shows peak values. Used by IsotopePatternView (for isotope pattern tool)
    '''
    def __init__(self, parent, peaks):
        super(IsoPatternPeakWidget, self).__init__(parent, ('m/z','int. (spectrum)','int. (calc.)', 'used'),
                                         ('{:10.5f}','{:11d}', '{:11d}', ''), peaks)

    def getData(self):
        data = []
        for row in range(self.rowCount()):
            try:
                intensity = 0
                if self.item(row, 1).text() != '':
                    intensity = int(self.item(row, 1).text())
                data.append((self.item(row, 0).text(), intensity, self.item(row, 2).text(),
                             self.item(row, 3).checkState() == Qt.CheckState.Checked))
            except ValueError:
                raise InvalidInputException('Intensities must be numeric', 'Incorrect entry: '+self.item(row, 1).text())
        return data

    def updateTable(self, newPeaks):
        self._peaks = newPeaks
        rowCount = self.rowCount()
        nrRows = len(self._peaks)-rowCount
        if nrRows>0:
            [self.insertRow(rowCount+i) for i in range(nrRows)]
        elif nrRows<0:
            [self.removeRow(rowCount-i-1) for i in range(abs(nrRows))]
        self.fill()

    def deleteLastPeak(self):
        for i, oldPeak in enumerate(self.getData()[:-1]):
            self._peaks[i][1] = oldPeak[1]
        self.updateTable(self._peaks[:-1])