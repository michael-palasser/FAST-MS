from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QTableWidget


class IonTableWidget(QTableWidget):
    def __init__(self, parrent, data, yPos):
        super(IonTableWidget, self).__init__(parrent)
        #self.headers = ['m/z', 'z', 'I', 'fragment', 'error /ppm', 'S/N', 'qual.']
        self.data = data
        self.setColumnCount(len(self.getHeaders()))
        self.move(20, yPos)  # 70
        self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.fill(data)
        self.setHorizontalHeaderLabels(self.getHeaders())
        self.resizeColumnsToContents()
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        # self.customContextMenuRequested['QPoint'].connect(partial(self.editRow, self, bools))

    def getHeaders(self):
        return ['m/z', 'z', 'I', 'fragment', 'error /ppm', 'S/N', 'qual.']

    def fill(self, data):
        self.setRowCount(len(data))
        for i, row in enumerate(data):
            for j, item in enumerate(row):
                newItem = QtWidgets.QTableWidgetItem(str(item))
                if j == 3:
                    newItem.setTextAlignment(QtCore.Qt.AlignLeft)
                else:
                    newItem.setTextAlignment(QtCore.Qt.AlignRight)
                newItem.setFlags(QtCore.Qt.ItemIsEnabled)
                self.setItem(i, j, newItem)
            """if args[0]:
                newItem = QtWidgets.QTableWidgetItem()
                newItem.setCheckState(args[0][0]) #QtCore.Qt.Unchecked
                self.setItem(i, len(row), newItem)"""
        self.resizeColumnsToContents()
        self.resizeRowsToContents()

class TickIonTableWidget(IonTableWidget):
    def __init__(self, parrent, data, yPos):
        #self.headers = ['m/z', 'z', 'I', 'fragment', 'error /ppm', 'S/N', 'qual.']
        super(TickIonTableWidget, self).__init__(parrent, data, yPos)

    def getHeaders(self):
        return super(TickIonTableWidget, self).getHeaders() + ['del.?']

    def fill(self, data):
        super(TickIonTableWidget, self).fill(data)
        for i, row in enumerate(data):
            newItem = QtWidgets.QTableWidgetItem()
            newItem.setCheckState(QtCore.Qt.Unchecked)  # QtCore.Qt.Unchecked
            print(i, len(row))
            self.setItem(i, len(row), newItem)
        self.resizeColumnsToContents()
        self.resizeRowsToContents()


    def getData(self):
        toDelete = []
        for row in range(self.rowCount()):
            print(self.item(row, self.columnCount()-1))
            if self.item(row, self.columnCount()-1).checkState():
                toDelete.append(self.hashRow(row))
                print(row)
        return toDelete

    def hashRow(self, row):
        return (self.item(row, 3).text(), int(self.item(row, 1).text()))