import time
from functools import partial

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QTableWidget
from math import log10


class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, data, parent=None):
        super(TableModel, self).__init__(parent)
        self._data = data
        self._formats = ['{:10.5f}','{:2d}', '{:12d}', '','{:4.2f}', '{:6.1f}', '{:4.2f}', '']


    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self._data[0]) if self.rowCount() else 0

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            i = index.row()
            j = index.column()

            if j == 2:
                currentData = self._data[i][j]
                formatString = self._format[2]
                if currentData >= 10 ** 13:
                    lg10 = str(int(log10(currentData) + 1))
                    formatString = '{:' + lg10 + 'd}'
                return formatString.format(currentData)
            else:
                return self._format[j].format(self._data[i][j])

            """if 0 <= row < self.rowCount():
                column = index.column()
                if 0 <= column < self.columnCount():
                    return self._data[row][column]"""




class IonTableWidget(QTableWidget):
    def __init__(self, parrent, data, yPos):
        super(IonTableWidget, self).__init__(parrent)
        print('starting')
        #self.headers = ['m/z', 'z', 'I', 'fragment', 'error /ppm', 'S/N', 'qual.']
        self._data = data
        self.setColumnCount(len(self.getHeaders()))
        self.move(20, yPos)  # 70
        self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.setRowCount(len(data))
        self._smallFnt = QFont()
        self._smallFnt.setPointSize(10)
        self._format = ['{:10.5f}','{:2d}', '{:12d}', '','{:4.2f}', '{:6.1f}', '{:4.2f}', '']
        start = time.time()
        for i, ion in enumerate(data):
            self.fill(i, ion)

        print(time.time()-start)
        self.setHorizontalHeaderLabels(self.getHeaders())
        self.resizeColumnsToContents()
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.setSortingEnabled(True)

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        print('done')
        # self.customContextMenuRequested['QPoint'].connect(partial(self.editRow, self, bools))

    def getHeaders(self):
        return ['m/z', 'z', 'I', 'fragment', 'error /ppm', 'S/N', 'qual.']

    def getValue(self,ion):
        return ion.getValues()

    def fill(self, row, ion):
        #print(self.getValue(ion))
        for j, item in enumerate(self.getValue(ion)):
            if j == 3 or j==7:
                newItem = QtWidgets.QTableWidgetItem(str(item))
                newItem.setTextAlignment(QtCore.Qt.AlignLeft)
                if j==7:
                    newItem.setFont(self._smallFnt)
            else:
                newItem = QtWidgets.QTableWidgetItem()
                newItem.setTextAlignment(QtCore.Qt.AlignRight)
                if j == 2:
                    formatString = self._format[2]
                    if item >= 10 ** 13:
                        lg10 = str(int(log10(item) + 1))
                        formatString = '{:' + lg10 + 'd}'
                    newItem.setData(QtCore.Qt.DisplayRole, formatString.format(item))
                else:
                    newItem.setData(QtCore.Qt.DisplayRole, self._format[j].format(item))
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




class TickIonTableWidget(IonTableWidget):
    def __init__(self, parrent, data, yPos):
        #self.headers = ['m/z', 'z', 'I', 'fragment', 'error /ppm', 'S/N', 'qual.']
        self.checkBoxes = []
        super(TickIonTableWidget, self).__init__(parrent, data, yPos)

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



class FinalIonTable(TickIonTableWidget):
    def getHeaders(self):
        return ['m/z', 'z', 'I', 'fragment', 'error /ppm', 'S/N', 'qual.','comment', 'del.?']

    def getValue(self,ion):
        return ion.getValues()+ [ion.comment]