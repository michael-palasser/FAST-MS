import sys
from functools import partial
from math import log10
import numpy as np

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QSortFilterProxyModel
import pandas as pd

from src.entities.Ions import FragmentIon, Fragment
from src.views.SpectrumView import SpectrumView


class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, data):
        super(TableModel, self).__init__()
        self._data = data
        #self._format = ['{:10.5f}','{:2d}', '{:12d}', '','{:4.2f}', '{:6.1f}', '{:4.2f}', '']
        self._format = ['{:10.5f}','{:2d}', '{:12d}', '','{:4.2f}', '{:6.1f}', '{:4.2f}', '']

    def data(self, index, role):
        if index.isValid():
            if role == Qt.DisplayRole:
                col = index.column()
                item = self._data.values[index.row()][col]
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
        return len(self._data.values)

    def columnCount(self, index):
        return self._data.columns.size





class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, ions, spectrum):
        super().__init__()
        self._ions = ions
        self._spectrum = spectrum

        self.table = QtWidgets.QTableView()
        valList, indizes = [], []
        for ion in pattern:
            valList.append(ion.getValues()+[ion.comment])
            indizes.append(self.hash(ion))
        shownData = pd.DataFrame(data=valList, columns=['mz','z','int','name','error','snr','qual','com'],
                                 index=pd.MultiIndex.from_tuples(indizes))
        print(shownData)
        self.model = TableModel(shownData)
        self.table.setModel(self.model)
        self.proxyModel = QSortFilterProxyModel()
        self.proxyModel.setSourceModel(self.model)

        self.table.setSortingEnabled(True)

        self.table.setModel(self.proxyModel)

        self.setCentralWidget(self.table)

    def connectTable(self, table):
        table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        table.customContextMenuRequested['QPoint'].connect(partial(self.showOptions, table))

    def hash(self, ion):
        return (ion.getName(),ion.charge)

    def showOptions(self, table, pos):
        global view
        """it = table.itemAt(pos)
        if it is None:
            return
        selectedRowIndex = it.row()
        columnCount = table.columnCount()
        item_range = QtWidgets.QTableWidgetSelectionRange(0, selectedRowIndex, columnCount - 1, selectedRowIndex)
        table.setRangeSelected(item_range, True)"""
        menu = QtWidgets.QMenu()
        showAction = menu.addAction("Show in Spectrum")
        delAction = menu.addAction("Delete/Undelete")
        action = menu.exec_(table.viewport().mapToGlobal(pos))
        if action == showAction:
            """index = None
            for i, t in enumerate(self._tables):
                if t == table:
                    index = i
            minLimit = 4000
            maxLimit = 0
            for ion in self._patterns[index].values():
                minMz = np.min(ion.isotopePattern['m/z'])
                maxMz = np.max(ion.isotopePattern['m/z'])
                if minLimit > minMz:
                    minLimit = minMz
                if maxLimit < maxMz:
                    maxLimit = maxMz"""
            ions = self.getIons(table)
            minLimit, maxLimit, YLimit = self.getLimits(ions)
            peaks = self._spectrum[np.where((self._spectrum[:,0]>(minLimit-5)) & (self._spectrum[:,0]<(maxLimit+5)))]
            view = SpectrumView(peaks, ions, minLimit, maxLimit, YLimit)



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
window=MainWindow(pattern)
window.show()
app.exec_()