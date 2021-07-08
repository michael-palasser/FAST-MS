import copy
from functools import partial
from math import log10

import pandas as pd
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt

from src.gui.IonTableWidgets import IonTableWidget
from src.gui.PeakWidgets import PeakWidget
from src.gui.ResultView import AbstractTableModel


class PeakTableModel(AbstractTableModel):
    '''
    TableModel for QTableView in SimplePeakView, used to show original peak values of remodelled ions
    '''
    def __init__(self, data):
        super(PeakTableModel, self).__init__(data, ('{:10.5f}', '{:11d}', '{:11d}', '{:4.2f}', ''),
                         ('m/z', 'int. (spectrum)', 'int. (calc.)', 'error /ppm', 'used'))
        self._data = data
        #print('data',data)
        #self._format = ['{:10.5f}', '{:11d}', '{:11d}','{:4.2f}', '']

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable


    def data(self, index, role):
        if index.isValid():
            if role == Qt.DisplayRole:
                col = index.column()
                item = self._data[index.row()][col]
                #print(item)
                formatString = self._format[col]
                if col == 1 or col ==2:
                    item = int(round(item))
                    if item >= 10 ** 12:
                        lg10 = str(int(log10(item) + 1))
                        formatString = '{:' + lg10 + 'd}'
                elif col==4:
                    if item:
                        return 'True'
                    return 'False'
                return formatString.format(item)
        if role == Qt.TextAlignmentRole:
            return Qt.AlignRight

    """def rowCount(self, index):
        return len(self._data.values)

    def columnCount(self, index):
        return self._data.columns.size

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return ('m/z','z','intensity','fragment','error /ppm', 'used')[section]"""


class SimplePeakView(QtWidgets.QWidget):
    '''
    Widget with QTableView showing original peak values of remodelled ions
    '''
    def __init__(self, parent, ion):
        super().__init__(parent)
        self._peaks = ion.getIsotopePattern()
        model = PeakTableModel(self._peaks)
        # self.proxyModel = QSortFilterProxyModel()
        # self.proxyModel.setSourceModel(_model)
        layout = QtWidgets.QVBoxLayout(self)
        self._table = QtWidgets.QTableView(self)
        self._table.setSortingEnabled(True)
        self._table.setModel(model)
        self._table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self._table.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        # self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self._table.customContextMenuRequested['QPoint'].connect(partial(self.showOptions, self._table))
        # self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        # self._table.move(0,0)
        #title = peaks[0][3] + ', ' + str(peaks[0][1])
        self.setObjectName(ion.getId())
        self._translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(self._translate(self.objectName(), self.objectName()))
        layout.addWidget(self._table)
        #self.resize(650, (len(self._peaks)) * 38 + 30)
        self.show()

    def showOptions(self, table, pos):
        menu = QtWidgets.QMenu()
        copyAction = menu.addAction("Copy Table")
        action = menu.exec_(table.viewport().mapToGlobal(pos))
        if action == copyAction:
            df=pd.DataFrame(data=self._peaks, columns=self._table.model().getHeaders())
            df.to_clipboard(index=False,header=True)


class PeakView(QtWidgets.QMainWindow):
    '''
    Window which is used in top-down search. It pops up when a user right-clicks on an ion in the table.
    User can then view the peak values, manually change intensities in the spectrum and re-modell the ion intensity.
    '''
    def __init__(self, parent, ion, model, save):
        super(PeakView, self).__init__(parent)
        self._ion = copy.deepcopy(ion)
        self._translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(self._translate(self.objectName(), ion.getName()+', '+str(ion.getCharge())))
        #self.centralwidget = QtWidgets.QWidget(self)
        self.setCentralWidget(QtWidgets.QWidget(self))
        self._verticalLayout = QtWidgets.QVBoxLayout(self.centralWidget())
        self._ionTable = IonTableWidget(self.centralWidget(),(self._ion,),30)
        self._peakTable = PeakWidget(self.centralWidget(), self._ion.getIsotopePattern())
        self._model = model
        self._save = save
        buttonWidget = QtWidgets.QWidget(self.centralWidget())
        horizontalLayout = QtWidgets.QHBoxLayout(buttonWidget)
        horizontalLayout.addWidget(self.makeBtn(buttonWidget,'Model',
                                'Model isotope distribution to peaks in spectrum', self.modelIon))
        horizontalLayout.addWidget(self.makeBtn(buttonWidget,'Save',
                                'Replaces old values with newly calculated ones', self.saveIon))
        #horizontalLayout.addWidget(self.makeIntensityWidget(self.centralWidget()))
        horizontalLayout.addItem(QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        self._verticalLayout.addWidget(buttonWidget)

        self._verticalLayout.addWidget(self._ionTable)
        self._verticalLayout.addWidget(self._peakTable)
        self.show()

    @staticmethod
    def makeBtn(parent, text, toolTip, fun):
        btn = QtWidgets.QPushButton(parent)
        btn.setText(text)
        btn.setToolTip(toolTip)
        btn.clicked.connect(fun)
        return btn

    def makeIntensityWidget(self, parent):
        widget = QtWidgets.QWidget(parent)
        horizontalLayout = QtWidgets.QHBoxLayout(widget)
        label = QtWidgets.QLabel(widget)
        label.setText(self._translate(self.objectName(), 'Int:'))
        horizontalLayout.addWidget(label)
        self._intInfo = QtWidgets.QLabel(widget)
        self._intInfo.setText(self._translate(self.objectName(), str(self._ion.getIntensity())))
        horizontalLayout.addWidget(self._intInfo)
        return widget


    def modelIon(self):
        vals = self._peakTable.readTable()
        newIon = self._model(copy.deepcopy(self._ion), vals)
        if self._ion.getIntensity() != newIon.getIntensity():
            self._ion = newIon
            self._peakTable.setPeaks(self._ion.getIsotopePattern())
            self._verticalLayout.removeWidget(self._ionTable)
            del self._ionTable
            self._ionTable =  IonTableWidget(self.centralWidget(),(self._ion,),30)
            self._verticalLayout.insertWidget(1, self._ionTable)
            #self._intInfo.setText(self._translate(self.objectName(), str(self._ion.getIntensity())))

    def saveIon(self):
        self._save(self._ion)
