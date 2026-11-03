from math import log10

from PySide6 import QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QTableWidget

from src.Exceptions import InvalidInputException
from src.gui.GUI_functions import connectTable, showOptions


class IonTableWidget(QTableWidget):
    '''
    Interactive ion table table for checking monoisotopic overlaps and to show ion values when "show peaks" is pressed
    (right click on ion table in top-down search).
    Parent class of IsoPatternIon and TickIonTableWidget
    '''
    def __init__(self, parent, ions, yPos):
        super(IonTableWidget, self).__init__(parent)
        self._ions = ions
        self.setColumnCount(len(self.getHeaders()))
        self.move(20, yPos)  # 70
        self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        self.setRowCount(len(ions))
        self._smallFnt = QFont()
        self._smallFnt.setPointSize(10)
        self._ionValues = []
        for i, ion in enumerate(ions):
            self.fill(i, ion)
        self.setHorizontalHeaderLabels(self.getHeaders())
        self.resizeColumnsToContents()
        self.setSortingEnabled(True)

    def getFormat(self):
        return ['{:10.5f}','{:2d}', '{:12d}', '','{:4.2f}', '{:6.1f}', '{:4.2f}', '']

    def getHeaders(self):
        return ['m/z','z','intensity','name','error /ppm', 'S/N','quality error']

    def getValue(self,ion):
        return ion.getValues()

    def fill(self, row, ion):
        '''
        Fills a row with data of an ion
        :param (int) row: index of the row
        :param (FragmentIon) ion:
        '''
        formats=self.getFormat()
        ionVal = []
        for j, item in enumerate(self.getValue(ion)):
            ionVal.append(item)
            if j == 3 or j==7:
                newItem = QtWidgets.QTableWidgetItem(str(item))
                newItem.setTextAlignment(Qt.AlignmentFlag.AlignLeft)
                if j==7:
                    newItem.setFont(self._smallFnt)
            else:
                newItem = QtWidgets.QTableWidgetItem()
                newItem.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                if j == 2:
                    formatString = formats[2]
                    if item >= 10 ** 13:
                        lg10 = str(int(log10(item) + 1))
                        formatString = '{:' + lg10 + 'd}'
                    newItem.setData(Qt.ItemDataRole.DisplayRole, formatString.format(item))
                else:
                    newItem.setData(Qt.ItemDataRole.DisplayRole, formats[j].format(item))
            newItem.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.setItem(row, j, newItem)
        self.resizeRowsToContents()
        self._ionValues.append(ionVal)

    def getIon(self, row):
        for ion in self._ions:
            if ion.getName() == self.item(row, 3).text() and ion.getCharge() == int(self.item(row, 1).text()):
                return ion

    def getData(self):
        itemList = []
        for row in range(self.rowCount()):
            itemList.append([self.item(row, col).text() for col in range(len(self.getHeaders()))])
        return itemList

class IsoPatternIon(IonTableWidget):
    '''
    Interactive ion table table for isotope pattern tool.
    '''
    def __init__(self, parent, ions, yPos):
        super(IsoPatternIon, self).__init__(parent, ions, yPos)
        connectTable(self, showOptions)

    def getFormat(self):
        return ['{:10.5f}','{:2d}', '{:12d}', '','{:4.2f}', '', '{:10.4f}','{:10.4f}']

    def getHeaders(self):
        return ['m/z','z','intensity','name','quality error', 'formula', 'neutral mass', 'av. mass']

    def fill(self, row, ion):
        '''
        Fills a row with data of an ion
        :param (int) row: index of the row
        :param (FragmentIon) ion:
        '''
        formats=self.getFormat()
        for j, item in enumerate(ion):
            if j == 3 or j==5:
                newItem = QtWidgets.QTableWidgetItem(str(item))
                newItem.setTextAlignment(Qt.AlignmentFlag.AlignLeft)
                newItem.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            else:
                newItem = QtWidgets.QTableWidgetItem()
                newItem.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                if j == 2:
                    formatString = formats[2]
                    if item >= 10 ** 13:
                        lg10 = str(int(log10(item) + 1))
                        formatString = '{:' + lg10 + 'd}'
                    newItem.setData(Qt.ItemDataRole.DisplayRole, formatString.format(item))
                else:
                    newItem.setData(Qt.ItemDataRole.DisplayRole, formats[j].format(item))
                    newItem.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            self.setItem(row, j, newItem)
        self.resizeRowsToContents()

    def getIntensity(self):
        if self._ions == ((),):
            return 1000
        try:
            return int(self.item(0,2).text())
        except ValueError:
            raise InvalidInputException('Unvalid intensity', self.item(0, 2).text())

    def getIon(self, row):
        return self._ions[row]

    def updateTable(self, newIons):
        self._ions = newIons
        for i, ion in enumerate(newIons):
            self.fill(i, ion)


class TickIonTableWidget(IonTableWidget):
    '''
    Interactive ion table table for checking overlapping ion clusters. Ticked ions are deleted.
    '''
    def __init__(self, parent, data, yPos):
        #self._headers = ['m/z', 'z', 'I', 'fragment', 'error /ppm', 'S/N', 'qual.']
        self.checkBoxes = []
        super(TickIonTableWidget, self).__init__(parent, data, yPos)

    def getHeaders(self):
        return super(TickIonTableWidget, self).getHeaders() + ['del.?']

    def fill(self, row, ion):
        '''
        Fills a row with data of an ion
        :param (int) row: index of the row
        :param (FragmentIon) ion:
        '''
        super(TickIonTableWidget, self).fill(row, ion)
        checkItem = QtWidgets.QTableWidgetItem()
        checkItem.setCheckState(Qt.CheckState.Unchecked)  # QtCore.Qt.CheckState.Unchecked
        self.setItem(row, len(self.getHeaders())-1, checkItem)
        self.checkBoxes.append((checkItem, ion))


    def getDumpList(self):
        dumpList = []
        for row in self.checkBoxes:
            if row[0].checkState() == Qt.CheckState.Checked:
                dumpList.append(row[1])
        return dumpList

    def getData(self):
        itemList = []
        columns = len(self.getHeaders())
        for row in range(self.rowCount()):
            items = [self.item(row, col).text() for col in range(columns-1)]
            items.append(self.item(row, columns-1).checkState() == Qt.CheckState.Checked)
            itemList.append(items)
        return itemList


class CalibrationIonTableWidget(QTableWidget):
    '''
    Interactive ion table table for choosing ions for calibration in CalibrationView
    '''
    def __init__(self, parent, ions):
        super(CalibrationIonTableWidget, self).__init__(parent)
        self._ions = ions
        self.setColumnCount(len(self.getHeaders()))
        self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        self.setRowCount(len(ions))
        self._ionValues = []
        for i, ion in enumerate(ions):
            self.fill(i, ion)
        self.setHorizontalHeaderLabels(self.getHeaders())
        self.resizeColumnsToContents()
        self.setSortingEnabled(True)
        connectTable(self, showOptions)


    def getFormat(self):
        return ['{:10.5f}','{:2d}', '{:12d}', '', '{:5.2f}', '']

    def getHeaders(self):
        return ['m/z','z','intensity','name','error /ppm', 'use']


    def fill(self, row, ionVals):
        '''
        Fills a row with data of an ion
        :param (int) row: index of the row
        :param (FragmentIon) ion:
        '''
        formats=self.getFormat()
        for j, item in enumerate(ionVals):
            if j == 3:
                newItem = QtWidgets.QTableWidgetItem(str(item))
                newItem.setTextAlignment(Qt.AlignmentFlag.AlignLeft)
            else:
                newItem = QtWidgets.QTableWidgetItem()
                newItem.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                if j == 2:
                    formatString = formats[2]
                    if item >= 10 ** 13:
                        lg10 = str(int(log10(item) + 1))
                        formatString = '{:' + lg10 + 'd}'
                    newItem.setData(Qt.ItemDataRole.DisplayRole, formatString.format(item))
                elif j == 5:
                    continue
                elif j == 6:
                    checkItem = QtWidgets.QTableWidgetItem()
                    if item:
                        checkItem.setCheckState(Qt.CheckState.Checked)  # Qt.CheckState.Unchecked
                    else:
                        checkItem.setCheckState(Qt.CheckState.Unchecked)  # Qt.CheckState.Unchecked
                    self.setItem(row, 5, checkItem)
                else:
                    newItem.setData(Qt.ItemDataRole.DisplayRole, formats[j].format(item))
            newItem.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.setItem(row, j, newItem)

    def checkStatus(self):
        itemList = []
        for row in range(self.rowCount()):
            itemList.append((self.item(row, 3).text(),int(self.item(row, 1).text()),self.item(row, 5).checkState()))
        return itemList

    def getData(self):
        data = []
        for i in range(self.rowCount()):
            data.append([self.item(i,j).text() for j in range(5)] + [self.item(i, 5).checkState() == Qt.CheckState.Checked])
            #itemList.append([self.item(row, col).text() for col in range(len(self.getHeaders()))])
        return data
