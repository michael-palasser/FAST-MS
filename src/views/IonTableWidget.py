from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QTableWidget
from math import log10
from src.top_down.IntensityModeller import IntensityModeller


class IonTableWidget(QTableWidget):
    def __init__(self, parrent, data, yPos):
        super(IonTableWidget, self).__init__(parrent)
        #self.headers = ['m/z', 'z', 'I', 'fragment', 'error /ppm', 'S/N', 'qual.']
        self.data = data
        self.setColumnCount(len(self.getHeaders()))
        self.move(20, yPos)  # 70
        self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)

        self.setRowCount(len(data))
        for i, ion in enumerate(data):
            self.fill(i, ion)
        self.setHorizontalHeaderLabels(self.getHeaders())
        self.resizeColumnsToContents()
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.setSortingEnabled(True)
        # self.customContextMenuRequested['QPoint'].connect(partial(self.editRow, self, bools))

    def getHeaders(self):
        return ['m/z', 'z', 'I', 'fragment', 'error /ppm', 'S/N', 'qual.']

    def getValue(self,ion):
        return ion.getValues()

    def fill(self, row, ion):
        print(self.getValue(ion))
        for j, item in enumerate(self.getValue(ion)):
            if j == 3 or j==7:
                newItem = QtWidgets.QTableWidgetItem(str(item))
                newItem.setTextAlignment(QtCore.Qt.AlignLeft)
            else:
                newItem = QtWidgets.QTableWidgetItem()
                if j == 0:
                    newItem.setData(QtCore.Qt.DisplayRole, '{:.5f}'.format(item))
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
                    newItem.setData(QtCore.Qt.DisplayRole, '{:5.1f}'.format(item))
                else:
                    newItem.setData(QtCore.Qt.DisplayRole, '{:2.2f}'.format(item))
                newItem.setTextAlignment(QtCore.Qt.AlignRight)
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
        self.setItem(row, len(self.getHeaders()), checkItem)
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

    """def hashRow(self, row):
        return (self.item(row, 3).text(), int(self.item(row, 1).text()))"""

class FinalIonTable(TickIonTableWidget):
    def getHeaders(self):
        return ['m/z', 'z', 'I', 'fragment', 'error /ppm', 'S/N', 'qual.','comment', 'del.?']

    def getValue(self,ion):
        return ion.getValues()+ [ion.comment]