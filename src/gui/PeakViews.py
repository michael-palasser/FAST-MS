import copy
from functools import partial
from math import log10

import pandas as pd
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt

from src.Exceptions import UnvalidInputException
from src.gui.IonTableWidget import IonTableWidget
from src.gui.ResultView import AbstractTableModel


class PeakTableModel(AbstractTableModel):
    def __init__(self, data):
        super(PeakTableModel, self).__init__(data,('{:10.5f}', '{:11d}', '{:11d}','{:4.2f}', ''),
                         ('m/z','int. (spectrum)','int. (calc.)','error /ppm', 'used'))
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
    def __init__(self, parent, ion):
        super().__init__(parent)
        self._peaks = ion.getIsotopePattern()
        model = PeakTableModel(self._peaks)
        # self.proxyModel = QSortFilterProxyModel()
        # self.proxyModel.setSourceModel(model)
        layout = QtWidgets.QVBoxLayout(self)
        self.table = QtWidgets.QTableView(self)
        self.table.setSortingEnabled(True)
        self.table.setModel(model)
        self.table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.table.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        # self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.table.customContextMenuRequested['QPoint'].connect(partial(self.showOptions, self.table))
        # self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        # self.table.move(0,0)
        #title = peaks[0][3] + ', ' + str(peaks[0][1])
        self.setObjectName(ion.getId())
        self._translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(self._translate(self.objectName(), self.objectName()))
        layout.addWidget(self.table)
        #self.resize(650, (len(self._peaks)) * 38 + 30)
        self.show()

    def showOptions(self, table, pos):
        menu = QtWidgets.QMenu()
        copyAction = menu.addAction("Copy Table")
        action = menu.exec_(table.viewport().mapToGlobal(pos))
        if action == copyAction:
            df=pd.DataFrame(data=self._peaks, columns=self.table.model().getHeaders())
            df.to_clipboard(index=False,header=True)


class PeakView(QtWidgets.QMainWindow):
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
        self.model = model
        self.save = save
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
        self.intInfo = QtWidgets.QLabel(widget)
        self.intInfo.setText(self._translate(self.objectName(), str(self._ion.getIntensity())))
        horizontalLayout.addWidget(self.intInfo)
        return widget


    def modelIon(self):
        vals = self._peakTable.readTable()
        newIon = self.model(copy.deepcopy(self._ion),vals)
        if self._ion.getIntensity() != newIon.getIntensity():
            self._ion = newIon
            self._peakTable.setPeaks(self._ion.getIsotopePattern())
            self._verticalLayout.removeWidget(self._ionTable)
            del self._ionTable
            self._ionTable =  IonTableWidget(self.centralWidget(),(self._ion,),30)
            self._verticalLayout.insertWidget(1, self._ionTable)
            #self.intInfo.setText(self._translate(self.objectName(), str(self._ion.getIntensity())))

    def saveIon(self):
        self.save(self._ion)


class GeneralPeakWidget(QtWidgets.QTableWidget):
    def __init__(self, parent, headers, format, peaks):
        super(GeneralPeakWidget, self).__init__(parent)
        self.headers = headers
        self._format = format
        self._peaks = peaks
        self.setWindowTitle('')
        self.setColumnCount(len(self.headers))
        self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.setRowCount(len(self._peaks))
        self.fill()
        self.setHorizontalHeaderLabels(self.headers)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.setSortingEnabled(True)
        self.customContextMenuRequested['QPoint'].connect(partial(self.showOptions, self))


    def fill(self):
        #print(self.getValue(ion))
        for row, peak in enumerate(self._peaks):
            for j, item in enumerate(peak):
                newItem = QtWidgets.QTableWidgetItem()
                newItem.setTextAlignment(QtCore.Qt.AlignRight)
                if j == 1 or j==2:
                    formatString = self._format[2]
                    item = int(round(item))
                    if item >= 10 ** 12:
                        lg10 = str(int(log10(item) + 1))
                        formatString = '{:' + lg10 + 'd}'
                    newItem.setData(QtCore.Qt.DisplayRole, formatString.format(item))
                    if j==2:
                        newItem.setFlags(QtCore.Qt.ItemIsEnabled)
                elif j==len(peak)-1:
                    newItem = QtWidgets.QTableWidgetItem()
                    if item:
                        newItem.setCheckState(QtCore.Qt.Checked)
                    else:
                        newItem.setCheckState(QtCore.Qt.Unchecked)
                else:
                    newItem.setData(QtCore.Qt.DisplayRole, self._format[j].format(item))
                    newItem.setFlags(QtCore.Qt.ItemIsEnabled)
                self.setItem(row, j, newItem)
        #self.resizeColumnsToContents()
        self.resizeRowsToContents()
        self.resizeColumnsToContents()


    def showOptions(self, table, pos):
        menu = QtWidgets.QMenu()
        copyAction = menu.addAction("Copy Table")
        action = menu.exec_(table.viewport().mapToGlobal(pos))
        if action == copyAction:
            #peaks.astype(float)
            df=pd.DataFrame(data=self._peaks, columns=self.headers)
            df['int. (spectrum)']= self._peaks['relAb']
            df['int. (calc.)']= self._peaks['calcInt']
            df['error /ppm']= self._peaks['error']
            df.to_clipboard(index=False,header=True)
            print(df)

    def readTable(self):
        itemList = []
        for row in range(self.rowCount()):
            itemList.append((int(self.item(row, 1).text()), int(self.item(row, 4).checkState()/2)==1))
        return itemList

    def setPeaks(self, peaks):
        self._peaks = peaks
        self.fill()

    def getPeaks(self):
        return self._peaks


class PeakWidget(GeneralPeakWidget):
    def __init__(self, parent, peaks):
        super(PeakWidget, self).__init__(parent, ('m/z','int. (spectrum)','int. (calc.)','error /ppm', 'used'),
                                         ('{:10.5f}','{:11d}', '{:11d}', '{:4.2f}', ''), peaks)


class IsoPatternPeakWidget(GeneralPeakWidget):
    def __init__(self, parent, peaks):
        super(IsoPatternPeakWidget, self).__init__(parent, ('m/z','int. (spectrum)','int. (calc.)', 'used'),
                                         ('{:10.5f}','{:11d}', '{:11d}', ''), peaks)
    def readTable(self):
        itemList = []
        for row in range(self.rowCount()):
            try:
                intensity = 0
                if self.item(row, 1).text() != '':
                    intensity = int(self.item(row, 1).text())
                itemList.append((intensity, int(self.item(row, 3).checkState()/2)==1, float(self.item(row, 0).text())))
            except ValueError:
                raise UnvalidInputException('Intensities must be numbers',self.item(row, 1).text())
        return itemList

    def showOptions(self, table, pos):
        menu = QtWidgets.QMenu()
        copyAction = menu.addAction("Copy Table")
        action = menu.exec_(table.viewport().mapToGlobal(pos))
        if action == copyAction:
            #peaks.astype(float)
            df=pd.DataFrame(data=self._peaks, columns=self.headers)
            df['int. (spectrum)']= self._peaks['relAb']
            df['int. (calc.)']= self._peaks['calcInt']
            df.to_clipboard(index=False,header=True)