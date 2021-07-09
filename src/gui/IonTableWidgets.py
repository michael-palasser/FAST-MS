from functools import partial
from math import log10
import pandas as pd

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QTableWidget

from src.Exceptions import InvalidInputException


class IonTableWidget(QTableWidget):
    '''
    Interactive ion table table for checking monoisotopic overlaps and to show ion values when "show peaks" is pressed
    (right click on ion table in top-down search).
    Parent class of IsoPatternIon and TickIonTableWidget
    '''
    def __init__(self, parent, ions, yPos):
        super(IonTableWidget, self).__init__(parent)
        #self.headers = ['m/z', 'z', 'I', 'fragment', 'error /ppm', 'S/N', 'qual.']
        self._ions = ions
        self.setColumnCount(len(self.getHeaders()))
        self.move(20, yPos)  # 70
        self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.setRowCount(len(ions))
        self._smallFnt = QFont()
        self._smallFnt.setPointSize(10)
        self._ionValues = []
        for i, ion in enumerate(ions):
            self.fill(i, ion)
        self.setHorizontalHeaderLabels(self.getHeaders())
        self.resizeColumnsToContents()
        #self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.setSortingEnabled(True)
        #self.customContextMenuRequested['QPoint'].connect(partial(self.showOptions, self))
        # self.customContextMenuRequested['QPoint'].connect(partial(self.editRow, self, bools))

    def getIonValues(self):
        return self._ionValues

    def getFormat(self):
        return ['{:10.5f}','{:2d}', '{:12d}', '','{:4.2f}', '{:6.1f}', '{:4.2f}', '']

    def getHeaders(self):
        return ['m/z','z','intensity','fragment','error /ppm', 'S/N','quality']

    def getValue(self,ion):
        return ion.getValues()

    def fill(self, row, ion):
        #print(self.getValue(ion))
        formats=self.getFormat()
        ionVal = []
        for j, item in enumerate(self.getValue(ion)):
            ionVal.append(item)
            if j == 3 or j==7:
                newItem = QtWidgets.QTableWidgetItem(str(item))
                newItem.setTextAlignment(QtCore.Qt.AlignLeft)
                if j==7:
                    newItem.setFont(self._smallFnt)
            else:
                newItem = QtWidgets.QTableWidgetItem()
                newItem.setTextAlignment(QtCore.Qt.AlignRight)
                if j == 2:
                    formatString = formats[2]
                    if item >= 10 ** 13:
                        lg10 = str(int(log10(item) + 1))
                        formatString = '{:' + lg10 + 'd}'
                    newItem.setData(QtCore.Qt.DisplayRole, formatString.format(item))
                else:
                    newItem.setData(QtCore.Qt.DisplayRole, formats[j].format(item))
                '''if j == 0:
                    newItem.setData(QtCore.Qt.DisplayRole, '{:10.5f}'.format(item))
                elif j == 1:
                    newItem.setData(QtCore.Qt.DisplayRole, '{:2d}'.format(item))
                elif j==2:
                    if item >= 10**13:
                        lg10 = str(int(log10(item)+1))
                        formatString = '{:'+lg10+'d}'
                        newItem.setData(QtCore.Qt.DisplayRole, formatString.format(item))
                    else:
                        newItem.setData(QtCore.Qt.DisplayRole, '{:12d}'.format(item))
                elif j == 5:
                    newItem.setData(QtCore.Qt.DisplayRole, '{:6.1f}'.format(item))
                else:
                    newItem.setData(QtCore.Qt.DisplayRole, '{:4.2f}'.format(item))
                newItem.setTextAlignment(QtCore.Qt.AlignRight)'''
            """if j == 3 or j == 7:
                newItem = QtWidgets.QTableWidgetItem(item)
                newItem.setTextAlignment(QtCore.Qt.AlignLeft)
            else:
                newItem = QtWidgets.QTableWidgetItem()
                newItem.setData(QtCore.Qt.DisplayRole, item)
                newItem.setTextAlignment(QtCore.Qt.AlignRight)"""
            newItem.setFlags(QtCore.Qt.ItemIsEnabled)
            self.setItem(row, j, newItem)
            """if args[0]:
                newItem = QtWidgets.QTableWidgetItem()
                newItem.setCheckState(QtCore.Qt.Unchecked) #QtCore.Qt.Unchecked
                self.setItem(i, len(ion), newItem)
                args[0][newItem] = ion"""
        #self.resizeColumnsToContents()
        self.resizeRowsToContents()
        self._ionValues.append(ionVal)

    def getIon(self, row):
        for ion in self._ions:
            if ion.getName() == self.item(row, 3).text() and ion.getCharge() == int(self.item(row, 1).text()):
                return ion

    '''def showOptions(self, table, pos):
        menu = QtWidgets.QMenu()
        copyAllAction = menu.addAction("Copy Table")
        copyAction = menu.addAction("Copy Cell")
        action = menu.exec_(table.viewport().mapToGlobal(pos))
        #ToDo
        if action == copyAction:
            it = table.indexAt(pos)
            if it is None:
                return
            selectedRow = it.row()
            selectedCol = it.column()
            df = pd.DataFrame([self._ionValues[selectedRow][selectedCol]])
            df.to_clipboard(index=False, header=False)
        if action == copyAllAction:
            df = pd.DataFrame(data=self._ionValues, columns=self.getHeaders())
            df.to_clipboard(index=False, header=True)'''



class IsoPatternIon(IonTableWidget):
    '''
    Interactive ion table table for isotope pattern tool.
    '''
    def getFormat(self):
        return ['{:10.5f}','{:2d}', '{:12d}', '','{:4.2f}', '', '{:10.4f}','{:10.4f}']

    def getHeaders(self):
        return ['m/z','z','intensity','name','quality', 'formula', 'neutral mass', 'av.mass']

    def fill(self, row, ion):
        formats=self.getFormat()
        for j, item in enumerate(ion):
            if j == 3 or j==5:
                newItem = QtWidgets.QTableWidgetItem(str(item))
                newItem.setTextAlignment(QtCore.Qt.AlignLeft)
                newItem.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            else:
                newItem = QtWidgets.QTableWidgetItem()
                newItem.setTextAlignment(QtCore.Qt.AlignRight)
                if j == 2:
                    formatString = formats[2]
                    if item >= 10 ** 13:
                        lg10 = str(int(log10(item) + 1))
                        formatString = '{:' + lg10 + 'd}'
                    newItem.setData(QtCore.Qt.DisplayRole, formatString.format(item))
                else:
                    newItem.setData(QtCore.Qt.DisplayRole, formats[j].format(item))
                    newItem.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            self.setItem(row, j, newItem)
        self.resizeRowsToContents()
        #self.customContextMenuRequested['QPoint'].connect(partial(self.showOptions, self))

    def getIntensity(self):
        if self._ions == ((),):
            return 1000
        try:
            return int(self.item(0,2).text())
        except ValueError:
            raise InvalidInputException('Unvalid Intensity', self.item(0, 2).text())


    def getIon(self, row):
        return self._ions[row]

    '''def showOptions(self, table, pos):
        menu = QtWidgets.QMenu()
        copyAllAction = menu.addAction("Copy Table")
        copyAction = menu.addAction("Copy Cell")
        action = menu.exec_(table.viewport().mapToGlobal(pos))
        if action == copyAction:
            it = table.indexAt(pos)
            if it is None:
                return
            selectedCol = it.column()
            df = pd.DataFrame([self._ions[0][selectedCol]])
            df.to_clipboard(index=False, header=False)
        elif action == copyAllAction:
            df = pd.DataFrame(data=self._ions, columns=self.getHeaders())
            df.to_clipboard(index=False, header=True)'''

    def updateTable(self, newIons):
        self._ions = newIons
        for i, ion in enumerate(newIons):
            self.fill(i, ion)


class TickIonTableWidget(IonTableWidget):
    '''
    Interactive ion table table for checking overlapping ion clusters.
    '''
    def __init__(self, parent, data, yPos):
        #self.headers = ['m/z', 'z', 'I', 'fragment', 'error /ppm', 'S/N', 'qual.']
        self.checkBoxes = []
        super(TickIonTableWidget, self).__init__(parent, data, yPos)

    def getHeaders(self):
        return super(TickIonTableWidget, self).getHeaders() + ['del.?']

    def fill(self, row, ion):
        super(TickIonTableWidget, self).fill(row, ion)
        checkItem = QtWidgets.QTableWidgetItem()
        checkItem.setCheckState(QtCore.Qt.Unchecked)  # QtCore.Qt.Unchecked
        self.setItem(row, len(self.getHeaders())-1, checkItem)
        #print(ion)
        self.checkBoxes.append((checkItem, ion))
        #self.resizeColumnsToContents()
        #self.resizeRowsToContents()


    def getDumpList(self):
        dumpList = []
        for row in self.checkBoxes:
            #checkBox = self.item(row, self.columnCount()-1)
            if row[0].checkState():
                dumpList.append(row[1])
        return dumpList



"""class FinalIonTable(TickIonTableWidget):
    def getHeaders(self):
        return ['m/z', 'z', 'I', 'fragment', 'error /ppm', 'S/N', 'qual.','comment', 'del.?']

    def getValue(self,ion):
        return ion.getValues()+ [ion.comment]"""