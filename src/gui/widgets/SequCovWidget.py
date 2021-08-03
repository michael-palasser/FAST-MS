import sys
import numpy as np
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import Qt, QVariant, QCoreApplication
from PyQt5.QtWidgets import QApplication

from src.gui.GUI_functions import connectTable, showOptions
from src.gui.tableviews.TableModels import AbstractTableModel


class SequCovPlotTableModel(AbstractTableModel):
    '''
    TableModel for a QTableView in SequCovWidget which shows if a fragment was found at a cleavage site
    '''
    def __init__(self, data, headers):
        super(SequCovPlotTableModel, self).__init__(data, (), headers)

    def data(self, index, role):
        '''
        Overwrites the data method of AbstractTableModel to correctly format each value
        '''
        if index.isValid():
            if role == Qt.DisplayRole:
                return self._data[index.row()][index.column()]
        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        if role == Qt.BackgroundRole:
            row,col = index.row(), index.column()
            if (row!=0) and (row!=len(self._data)-1) and (col!=0):
                if self._data[row][col]==1:
                    return QVariant(QtGui.QColor(Qt.green))
                elif self._data[row][col]==0:
                    return QVariant(QtGui.QColor(Qt.red))


class SequCovTableModel(AbstractTableModel):
    '''
    TableModel for a QTableView in SequCovWidget which shows the sequence coverage for each fragment type
    '''
    def __init__(self, data):
        super(SequCovTableModel, self).__init__(data, (), ('fragm. type', 'sequ.cov. /%'))

    def data(self, index, role):
        '''
        Overwrites the data method of AbstractTableModel to correctly format each value
        '''
        if index.isValid():
            if role == Qt.DisplayRole:
                col = index.column()
                item = self._data[index.row()][col]
                if col == 0:
                    return item
                # print(item)
                return '{:2.1f}'.format(item)
        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter


class SequCovWidget(QtWidgets.QWidget):
    '''
    Widget which shows all sequence coverage details
    '''
    def __init__(self, values, sequence, fragmentData, globalData):
        super().__init__(parent=None)
        verticalLayout = QtWidgets.QVBoxLayout(self)
        model = SequCovTableModel(values)
        table = QtWidgets.QTableView(self)
        table.setModel(model)
        #table.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        table.resizeColumnsToContents()
        table.setSortingEnabled(True)
        [table.setRowHeight(i,23) for i in range(len(values))]
        table.setMinimumHeight((len(values)+1)*23)
        connectTable(table,showOptions)
        verticalLayout.addWidget(table)

        verticalLayout.addWidget(self.makeCoverageTable(fragmentData, ['fragm.'] + sequence))
        verticalLayout.addWidget(self.makeCoverageTable(globalData, ['direction'] + sequence))
        self._translate = QCoreApplication.translate
        self.setObjectName('Sequence Coverage')
        self.setWindowTitle(self._translate(self.objectName(), self.objectName()))
        self.show()

    def makeCoverageTable(self, data, headers):
        model = SequCovPlotTableModel(data, headers)
        table = QtWidgets.QTableView(self)
        # self._table.setSortingEnabled(True)
        table.setModel(model)
        #table.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        table.resizeColumnsToContents()
        table.setColumnWidth(0,70)
        table.resizeRowsToContents()
        connectTable(table,showOptions)
        #table.resize(70+len(data[0])*table.columnWidth(1), (len(data)+1)*table.rowHeight(0))
        return table


def processCoverageData(sequ, dataDict):
    sequLength = len(sequ)
    data = [[''] + [str(i + 1) for i in range(sequLength)]]
    for key, line in dataDict.items():
        data.append([key] + list(line))
    data.append([''] + [str(sequLength - i) for i in range(sequLength)])
    return data

if __name__ == '__main__':
    app = QApplication(sys.argv)
    sequ = list('GGCUGCUUGUCCUUUAAUGGUCCAGUC')
    overall = [(key,val*100) for key,val in
               {'a': 0.7692307692307693, 'c': 0.9230769230769231, 'w': 0.7692307692307693, 'y': 0.9230769230769231, 'allForward': 0.9615384615384616, 'allBackward': 0.9230769230769231, 'all': 0.9259259259259259}.items()]
    gui = SequCovWidget( overall,
                         sequ, processCoverageData(sequ, {'a': np.array([0., 1., 0., 1., 1., 1., 0., 1., 1., 1., 0., 0., 1., 0., 1., 1., 1.,
       1., 1., 1., 1., 1., 1., 1., 1., 1., np.nan]), 'c': np.array([0., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
       1., 1., 1., 1., 1., 0., 1., 1., 1.,np.nan]), 'w': np.array([np.nan,1., 1., 0., 0., 1., 1., 0., 1., 1., 0., 1., 1., 1., 1., 1., 1., 1.,
       0., 1., 1., 1., 1., 1., 1., 1., 0.]), 'y': np.array([np.nan,1., 1., 1., 1., 1., 1., 1., 1., 1., 0., 1., 1., 1., 1., 1., 1., 1.,
       1., 1., 1., 1., 1., 1., 1., 1., 0.])}),
                         processCoverageData(sequ, {
                             'forward': np.array([0., 1., 0., 1., 1., 1., 0., 1., 1., 1., 0., 0., 1., 0., 1., 1., 1.,
                                            1., 1., 1., 1., 1., 1., 1., 1., 1., np.nan]),
                             'backward': np.array([np.nan,1., 1., 1., 1., 1., 1., 1., 1., 1., 0., 1., 1., 1., 1., 1., 1., 1.,
                                            1., 1., 1., 1., 1., 1., 1., 1., 0.])}))
    sys.exit(app.exec_())