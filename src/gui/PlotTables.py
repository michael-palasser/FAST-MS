from functools import partial
from math import isnan

import pandas as pd
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt

from src.gui.ResultView import AbstractTableModel


class PlotTableModel(AbstractTableModel):
    def __init__(self, data, keys, precision):
        self.ionTypes = len(keys)
        #print(data, '\n', data[0][len(data)-1])
        valFormat = '{:2.'+str(precision)+'f}'
        format = ['','{:2d}']+self.ionTypes*[valFormat]+['{:2d}','',]
        headers = ['sequ. (f)','cleav.side (f)'] + keys + ['cleav.side (b)','sequ. (b)']
        super(PlotTableModel, self).__init__(data,format, headers)

    def data(self, index, role):
        if index.isValid():
            if role == Qt.DisplayRole:
                col = index.column()
                item = self._data[index.row()][col]
                if col == 0 or col == len(self._data[0])-1:
                    return item
                #print(item)
                elif isnan(item):
                    return ''
                return self._format[col].format(item)


class PlotTableView(QtWidgets.QWidget):
    def __init__(self, data, keys, title, precision):
        super().__init__(parent=None)
        verticalLayout = QtWidgets.QVBoxLayout(self)
        scrollArea = QtWidgets.QScrollArea(self)
        #scrollArea.setGeometry(QtCore.QRect(10, 10, len(data[0])*50+200, len(data)*22+25))
        scrollArea.setWidgetResizable(True)
        # scrollArea.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        # scrollArea.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        model = PlotTableModel(data, keys,precision)
        self.table = QtWidgets.QTableView(self)
        self.table.setSortingEnabled(True)
        self.table.setModel(model)
        self.table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.table.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        #self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.table.customContextMenuRequested['QPoint'].connect(partial(self.showOptions, self.table))
        scrollArea.setWidget(self.table)
        #self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        #self.table.move(0,0)
        self.setObjectName(title)
        self._translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(self._translate(self.objectName(), self.objectName()))
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        verticalLayout.addWidget(scrollArea)
        #self.resize(len(data[0])*50+200, len(data)*22+25)
        self.show()

    def showOptions(self, table, pos):
        menu = QtWidgets.QMenu()
        copyAction = menu.addAction("Copy Table")
        action = menu.exec_(table.viewport().mapToGlobal(pos))
        if action == copyAction:
            df=pd.DataFrame(data=self.table.model().getData(), columns=self.table.model().getHeaders())
            df.to_clipboard(index=False,header=True)