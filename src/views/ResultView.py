import sys
from functools import partial
from math import log10
import numpy as np

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QSortFilterProxyModel
import pandas as pd
from PyQt5.QtGui import QStandardItem
from PyQt5.QtWidgets import QAbstractItemView

from src.entities.Ions import FragmentIon, Fragment
from src.views.SpectrumView import SpectrumView


class IonTableModel(QtCore.QAbstractTableModel):
    def __init__(self, data):
        super(IonTableModel, self).__init__()
        self._data = data
        #self._format = ['{:10.5f}','{:2d}', '{:12d}', '','{:4.2f}', '{:6.1f}', '{:4.2f}', '']
        self._format = ['{:10.5f}','{:2d}', '{:12d}', '','{:4.2f}', '{:6.1f}', '{:4.2f}', '{:4.2f}', '']
        """for i, header in enumerate(('m/z','z','intensity','fragment','error /ppm', 'S/N','quality',
                                                        'formula','score', 'comment')):
            self.setHeaderData(i, Qt.Horizontal, header)"""
        self._headers = ('m/z','z','intensity','fragment','error /ppm', 'S/N','quality', 'score', 'comment')
        self.setHeaderData(0, QtCore.Qt.Horizontal, "Test")

    """def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable"""

    def data(self, index, role):
        if index.isValid():
            if role == Qt.DisplayRole:
                col = index.column()
                #item = self._data.values[index.row()][col]
                item = self._data[index.row()][col]
                formatString = self._format[col]
                if col == 3 or col == 7:
                    return item
                if col == 2 :
                    if item >= 10 ** 13:
                        lg10 = str(int(log10(item) + 1))
                        formatString = '{:' + lg10 + 'd}'
                    return formatString.format(item)
                return formatString.format(item)

    def rowCount(self, index):
        #return len(self._data.values)
        return len(self._data)

    def columnCount(self, index):
        #return self._data.columns.size
        return len(self._data[0])

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self._headers[section]

    def getHashOfRow(self, rowIndex):
        #nameIndex = self.index(rowIndex, 3)
        #chargeIndex = self.index(rowIndex, 1)
        #return self._data.index[rowIndex]
        return (self._data[rowIndex][3],self._data[rowIndex][1])

    def sort(self, Ncol, order):
        """Sort table by given column number."""
        self.layoutAboutToBeChanged.emit()
        print(Ncol)
        #self._data = self._data.sort_values(self._headers[Ncol], ascending=order == Qt.AscendingOrder)
        if order == Qt.AscendingOrder:
            self._data.sort(key= lambda tup:tup[Ncol])
        else:
            self._data.sort(key= lambda tup:tup[Ncol], reverse=True)
        self.layoutChanged.emit()



    def addData(self, newRow):
        self._data.append(newRow)

    def removeData(self, indexToRemove):
        del self._data[indexToRemove]




class PeakTableModel(QtCore.QAbstractTableModel):
    def __init__(self, data):
        super(PeakTableModel, self).__init__()
        self._data = data
        #self._format = ['{:10.5f}','{:2d}', '{:12d}', '','{:4.2f}', '{:6.1f}', '{:4.2f}', '']
        self._format = ['{:10.5f}','{:2d}', '{:11d}', '','{:4.2f}', '{:6.1f}', '{:4.2f}', '']
        self.setHeaderData(0, QtCore.Qt.Horizontal, "Test")

    def flags(self, index):
        return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def data(self, index, role):
        if index.isValid():
            if role == Qt.DisplayRole:
                col = index.column()
                item = self._data.values[index.row()][col]
                formatString = self._format[col]
                if col == 3:
                    return item
                if col == 2 :
                    if item >= 10 ** 12:
                        lg10 = str(int(log10(item) + 1))
                        formatString = '{:' + lg10 + 'd}'
                    return formatString.format(item)
                return formatString.format(item)

    def rowCount(self, index):
        return len(self._data.values)

    def columnCount(self, index):
        return self._data.columns.size

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return ('m/z','z','intensity','fragment','error /ppm', 'used')[section]


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, ions, deletedIons, spectrum):
        super().__init__()
        #self._ions = ions
        #self._deletedIons = deletedIons
        #self._spectrum = spectrum
        #{self.hash(ion): ion for ion in ions}
        """valList, indizes = [], []
        for ion in ions:
            valList.append(ion.getMoreValues())
            indizes.append(self.hash(ion))
        shownData = pd.DataFrame(data=valList, columns=['mz','z','int','name','error','snr','qual','com'],
                                 index=pd.MultiIndex.from_tuples(indizes))"""
        #self.table = self.makeTable(shownData)
        """self.table = self.makeTable(self._ions)
        self.delTable = self.makeTable(self._deletedIons)"""
        self.tables = [self.makeTable(ions), self.makeTable(deletedIons)]
        self.setCentralWidget(self.tables[0])

    def makeTable(self, data):
        model = IonTableModel([ion.getMoreValues() for ion in data.values()])
        self.proxyModel = QSortFilterProxyModel()
        self.proxyModel.setSourceModel(model)
        table = QtWidgets.QTableView()
        table.setModel(model)
        table.setSortingEnabled(True)
        #table.setModel(self.proxyModel)
        self.connectTable(table)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        return table


    def connectTable(self, table):
        table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        table.customContextMenuRequested['QPoint'].connect(partial(self.showOptions, table))

    def hash(self, ion):
        return (ion.getName(),ion.charge)

    def showOptions(self, table, pos):
        global view
        menu = QtWidgets.QMenu()
        showAction = menu.addAction("Show in Spectrum")
        peakAction = menu.addAction("Show Peaks")
        actionStrings = ["Delete", "Restore"]
        mode = 0
        other = 1
        if table != self.table:
            mode = 1
            other = 0
        delAction = menu.addAction(actionStrings[mode])
        action = menu.exec_(table.viewport().mapToGlobal(pos))
        it = table.indexAt(pos)
        if it is None:
            return
        selectedRow = it.row()
        selectedHash = table.model().getHashOfRow(selectedRow)
        if action == showAction:
            ions = self.getIons(self._ions[selectedHash])
            print(ions)
            minLimit, maxLimit, maxY = self.getLimits(ions)
            peaks = self._spectrum[np.where((self._spectrum[:,0]>(minLimit-5)) & (self._spectrum[:,0]<(maxLimit+5)))]
            view = SpectrumView(peaks, ions, np.min(self._ions[selectedHash].isotopePattern['m/z']),
                                np.max(self._ions[selectedHash].isotopePattern['m/z']),
                                np.max(self._ions[selectedHash].isotopePattern['relAb']))
        elif action == peakAction:
            pass
            #self.peakView = PeakView(self._ions[selectedHash].getPeaks())
            """print(ions)
            minLimit, maxLimit, maxY = self.getLimits(ions)
            peaks = self._spectrum[np.where((self._spectrum[:,0]>(minLimit-5)) & (self._spectrum[:,0]<(maxLimit+5)))]
            view = SpectrumView(peaks, ions, np.min(self._ions[selectedHash].isotopePattern['m/z']),
                                np.max(self._ions[selectedHash].isotopePattern['m/z']),
                                np.max(self._ions[selectedHash].isotopePattern['relAb']))"""
        elif action == delAction:
            #actionString = actionString[:-1]+'ing '
            choice = QtWidgets.QMessageBox.question(self, "",
                                        actionStrings[mode][:-1]+'ing '+self._ions[selectedHash].getName()+"?",
                                        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if choice == QtWidgets.QMessageBox.Yes:
                ionLists = [self._ions, self._deletedIons]
                comments = ['man.del.','man.undel.']
                ionToDelete = ionLists[mode][selectedHash]
                ionToDelete.comment += comments[mode]
                ionLists[other][selectedHash] = ionToDelete
                del ionLists[mode][selectedHash]

                #self.table.model().removeRow(selectedRow)
                table.model().removeData(selectedRow)
                table.model().addData(ion.getMoreValues())
                print('deleted',selectedRow, selectedHash)



class PeakView(QtWidgets.QWidget):
    def __init__(self, peaks):
        super().__init__()
        self._peaks = peaks
        model =PeakTableModel(peaks)
        self.proxyModel = QSortFilterProxyModel()
        self.proxyModel.setSourceModel(model)
        self.table = QtWidgets.QTableView()
        self.table.setSortingEnabled(True)
        self.table.setModel(self.proxyModel)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.show()





pattern = [FragmentIon(Fragment('a', 3, "", '', [], 0), 1, [], 0),
                    FragmentIon(Fragment('a', 5, "-G", '', [], 0), 1, [], 0),
                    FragmentIon(Fragment('b', 5, "", '', [], 0), 1, [], 0),
                    FragmentIon(Fragment('b', 5, "-G", '', [], 0), 1, [], 0)]

for i, ion in enumerate(pattern):
    ion.intensity = 3 * 10 ** 6 * (i + 1) + i * 100
    ion.error = i + 0.01
    ion.quality = 0.5 - i / 100
    ion.noise = 10 ** 6 * 2
    print(ion.getValues())


app=QtWidgets.QApplication(sys.argv)
window=MainWindow({(ion.getName(),ion.charge): ion for ion in pattern},
                  {(ion.getName(),ion.charge): ion for ion in pattern}, [])
window.show()
app.exec_()