import sys
from functools import partial
from math import log10, isnan
import numpy as np
try:
    from Tkinter import Tk
except ImportError:
    from tkinter import Tk
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QSortFilterProxyModel
import pandas as pd
from PyQt5.QtGui import QStandardItem
from PyQt5.QtWidgets import QAbstractItemView

from src.entities.Ions import FragmentIon, Fragment
from src.views.SpectrumView import SpectrumView

class AbstractTableModel(QtCore.QAbstractTableModel):
    def __init__(self, data, format, headers):
        super(AbstractTableModel, self).__init__()
        self._data = data
        self._format = format
        self._headers = headers

    def data(self, index, role):
        if index.isValid():
            if role == Qt.DisplayRole:
                col = index.column()
                item = self._data[index.row()][col]
                formatString = self._format[col]
                return formatString.format(item)

    def getData(self):
        return self._data

    def getHeaders(self):
        return self._headers

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

    def sort(self, Ncol, order):
        """Sort table by given column number."""
        self.layoutAboutToBeChanged.emit()
        #self._data = self._data.sort_values(self._headers[Ncol], ascending=order == Qt.AscendingOrder)
        if order == Qt.AscendingOrder:
            self._data.sort(key= lambda tup:tup[Ncol])
        else:
            self._data.sort(key= lambda tup:tup[Ncol], reverse=True)
        self.layoutChanged.emit()


class IonTableModel(AbstractTableModel):
    def __init__(self, data, precRegion, maxQual, maxScore):
        super(IonTableModel, self).__init__(data, ('{:10.5f}','{:2d}', '{:12d}', '','{:4.2f}', '{:6.1f}', '{:4.2f}',
               '{:4.1f}', ''), ('m/z','z','intensity','fragment','error /ppm', 'S/N','quality', 'score', 'comment'))
        self._precRegion = precRegion
        self._maxQual = maxQual
        self._maxScore = maxScore

    """def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable"""

    def data(self, index, role):
        if index.isValid():
            if role == Qt.DisplayRole:
                col = index.column()
                item = self._data[index.row()][col]
                formatString = self._format[col]
                if col == 3 or col == 8:
                    return item
                if col == 2 :
                    if item >= 10 ** 13:
                        lg10 = str(int(log10(item) + 1))
                        formatString = '{:' + lg10 + 'd}'
                    return formatString.format(item)
                return formatString.format(item)
        if role == Qt.TextAlignmentRole:
            if index.column() == 3 or index.column() == 8:
                return Qt.AlignLeft
            else:
                return Qt.AlignRight
        if role == Qt.FontRole:
            if index.column() == 8:
                font = QtGui.QFont()
                font.setPointSize(10)
                return font
        if role == Qt.ForegroundRole:
            col = index.column()
            item = self._data[index.row()][col]
            if col == 0:
                if self._precRegion[0]<item<self._precRegion[1]:
                    return QtGui.QColor('red')
            if col == 6:
                if item > self._maxQual:
                    return QtGui.QColor('red')
            if col == 7:
                if item > self._maxScore:
                    return QtGui.QColor('red')

    def getHashOfRow(self, rowIndex):
        return (self._data[rowIndex][3],self._data[rowIndex][1])

    def getRow(self, rowIndex):
        return self._data[rowIndex]

    def addData(self, newRow):
        self._data.append(newRow)

    def removeData(self, indexToRemove):
        #self.removeRow(indexToRemove)
        del self._data[indexToRemove]


class PeakTableModel(AbstractTableModel):
    def __init__(self, data):
        super(PeakTableModel, self).__init__(data,('{:10.5f}','{:2d}', '{:11d}', '','{:4.2f}', '{:6.1f}', '{:4.2f}', ''),
                         ('m/z','z','intensity','fragment','error /ppm', 'used'))
        self._data = data
        #print('data',data)
        #self._format = ['{:10.5f}','{:2d}', '{:12d}', '','{:4.2f}', '{:6.1f}', '{:4.2f}', '']
        self._format = ['{:10.5f}','{:2d}', '{:11d}', '','{:4.2f}', '{:6.1f}', '{:4.2f}', '']

    def flags(self, index):
        return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def data(self, index, role):
        if index.isValid():
            if role == Qt.DisplayRole:
                col = index.column()
                item = self._data[index.row()][col]
                #print(item)
                formatString = self._format[col]
                if col == 3:
                    return item
                if col == 2 :
                    if item >= 10 ** 12:
                        lg10 = str(int(log10(item) + 1))
                        formatString = '{:' + lg10 + 'd}'
                    return formatString.format(item)
                return formatString.format(item)

    """def rowCount(self, index):
        return len(self._data.values)

    def columnCount(self, index):
        return self._data.columns.size

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return ('m/z','z','intensity','fragment','error /ppm', 'used')[section]"""


class ResultsWindow(QtWidgets.QMainWindow):
    def __init__(self, ions, deletedIons, spectrum, main):
        super().__init__()
        self._ions = ions
        self._deletedIons = deletedIons
        self._spectrum = spectrum
        self._main = main
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
        self.setUpUi()
        self.createMenuBar()
        #self.tables = [self.makeTable(ions), self.makeTable(_deletedIons)]
        self.tables = []
        for table, name in zip((self._ions, self._deletedIons), ('Observed Ions', 'Deleted Ions')):
            self.makeTabWidget(table, name)

        self.formlayout.addWidget(self.tabWidget)
        #self.setCentralWidget(self.tables[0])

    def setUpUi(self):
        self.setObjectName("Results")
        self._translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(self._translate(self.objectName(), self.objectName()))
        self.centralwidget = QtWidgets.QWidget(self)
        self.formlayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        #self.formlayout.addWidget(self.tabWidget)
        self.setCentralWidget(self.centralwidget)

        self.resize(1000, 900)

        #self.formLayout = QtWidgets.QFormLayout(self.centralwidget)
        #self.mainWindow.setStatusBar(QtWidgets.QStatusBar(self.mainWindow))


    def createMenuBar(self):
        self.menubar = QtWidgets.QMenuBar(self)
        self.setMenuBar(self.menubar)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 340, 22))
        self.createMenu("File", {'Save':self.dumb, 'Export to xlsx':self.dumb, 'Export to txt':self.dumb,
                                 'Close':self.dumb}, ['','','',''], ["Ctrl+S",'','',"Ctrl+Q"])
        self.createMenu("Edit", {'Copy Table':self.dumb, 'Re-model':self.dumb},
                        ['', 'Repeat overlap modelling involving user inputs'], ["Ctrl+C",""])
        self.createMenu("Show", {'Occupancy-Plot':self.dumb, 'Charge-Plot':self.dumb},
                        ['Show occupancies as a function of sequence pos.',
                         'Show av. charge as a function of sequence pos.'], ["",""])

    def dumb(self):
        print('not yet implemented')

    def createMenu(self, name, options, tooltips, shortcuts):
        menu = QtWidgets.QMenu(self.menubar)
        menu.setTitle(self._translate(self.objectName(), name))
        #menuActions = dict()
        pos = len(options)
        for i, option in enumerate(options.keys()):
            action = QtWidgets.QAction(self)
            action.setText(self._translate(self.objectName(),option))
            if tooltips[i] != "":
                action.setToolTip(tooltips[i])
            if shortcuts[i] != "":
                action.setShortcut(shortcuts[i])
            action.triggered.connect(options[option])
            #menuActions[option] = action
            menu.addAction(action)
            pos -= 1
        self.menubar.addAction(menu.menuAction())
        return menu#, menuActions

    def makeTabWidget(self, data, name):
        tab = QtWidgets.QWidget()
        self.tabWidget.addTab(tab, "")
        self.tabWidget.setTabText(self.tabWidget.indexOf(tab), self._translate(self.objectName(), name))
        scrollArea = QtWidgets.QScrollArea(tab)
        scrollArea.setGeometry(QtCore.QRect(10, 10, 950, 800))
        scrollArea.setWidgetResizable(True)
        #scrollArea.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        #scrollArea.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        table = self.makeTable(scrollArea, data)
        scrollArea.setWidget(table)
        self.tables.append(table)

        self.tabWidget.setEnabled(True)


    def makeTable(self, parent, data):
        model = IonTableModel([ion.getMoreValues() for ion in data.values()])
        #self.proxyModel = QSortFilterProxyModel()
        #self.proxyModel.setSourceModel(model)
        table = QtWidgets.QTableView(parent)
        table.setModel(model)
        table.setSortingEnabled(True)
        #table.setModel(self.proxyModel)
        self.connectTable(table)
        #table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        table.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        return table


    def connectTable(self, table):
        table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        table.customContextMenuRequested['QPoint'].connect(partial(self.showOptions, table))

    def hash(self, ion):
        return (ion.getName(),ion.charge)

    def showOptions(self, table, pos):
        menu = QtWidgets.QMenu()
        showAction = menu.addAction("Show in Spectrum")
        peakAction = menu.addAction("Show Peaks")
        copyAction = menu.addAction("Copy Table")
        actionStrings = ["Delete", "Restore"]
        mode = 0
        other = 1
        if table != self.tables[0]:
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
            global spectrumView
            ions = self.getIons(self._ions[selectedHash])
            minLimit, maxLimit, maxY = self.getLimits(ions)
            peaks = self._spectrum[np.where((self._spectrum[:,0]>(minLimit-5)) & (self._spectrum[:,0]<(maxLimit+5)))]
            spectrumView = SpectrumView(peaks, ions, np.min(self._ions[selectedHash].isotopePattern['m/z']),
                                np.max(self._ions[selectedHash].isotopePattern['m/z']),
                                np.max(self._ions[selectedHash].isotopePattern['relAb']))
        elif action == peakAction:
            global peakview
            pass
            #peakview = PeakView(self._ions[selectedHash].getPeaks())
        elif action == copyAction:
            df=pd.DataFrame(data=table.model().getData(), columns=table.model().getHeaders())
            df.to_clipboard(index=False,header=True)
        elif action == delAction:
            ionLists = [self._ions, self._deletedIons]
            comments = ['man.del.','man.undel.']
            ionToDelete = ionLists[mode][selectedHash]
            #actionString = actionString[:-1]+'ing '
            choice = QtWidgets.QMessageBox.question(self, "",
                                        actionStrings[mode][:-1]+'ing '+ionLists[mode][selectedHash].getName()+"?",
                                        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if choice == QtWidgets.QMessageBox.Yes:
                ionToDelete.comment += comments[mode]
                ionLists[other][selectedHash] = ionToDelete
                del ionLists[mode][selectedHash]
                table.model().removeData(selectedRow)
                self.tables[other].model().addData(ionToDelete.getMoreValues())
                print(actionStrings[mode]+"d",selectedRow, selectedHash)



class PeakView(QtWidgets.QWidget):
    def __init__(self, peaks):
        super().__init__(parent=None)
        model = PeakTableModel(peaks)
        #self.proxyModel = QSortFilterProxyModel()
        #self.proxyModel.setSourceModel(model)
        self.table = QtWidgets.QTableView(self)
        self.table.setSortingEnabled(True)
        self.table.setModel(model)
        self.table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.table.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        #self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.table.customContextMenuRequested['QPoint'].connect(partial(self.showOptions, self.table))
        #self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        #self.table.move(0,0)
        title = peaks[0][3] + ', ' + str(peaks[0][1])
        self.setObjectName(title)
        self._translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(self._translate(self.objectName(), self.objectName()))
        self.resize(650, (len(peaks))*38+30)
        self.show()

    def showOptions(self, table, pos):
        menu = QtWidgets.QMenu()
        copyAction = menu.addAction("Copy Table")
        action = menu.exec_(table.viewport().mapToGlobal(pos))
        if action == copyAction:
            df=pd.DataFrame(data=self.table.model().getData(), columns=self.table.model().getHeaders())
            df.to_clipboard(index=False,header=True)


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

        scrollArea = QtWidgets.QScrollArea(self)
        scrollArea.setGeometry(QtCore.QRect(10, 10, len(data[0])*50+200, len(data)*22+25))
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
        self.resize(len(data[0])*50+200, len(data)*22+25)
        self.show()

    def showOptions(self, table, pos):
        menu = QtWidgets.QMenu()
        copyAction = menu.addAction("Copy Table")
        action = menu.exec_(table.viewport().mapToGlobal(pos))
        if action == copyAction:
            df=pd.DataFrame(data=self.table.model().getData(), columns=self.table.model().getHeaders())
            df.to_clipboard(index=False,header=True)


if __name__ == '__main__':

    """pattern = [FragmentIon(Fragment('a', 3, "", '', [], 0), 1, [], 0),
                        FragmentIon(Fragment('a', 5, "-G", '', [], 0), 1, [], 0),
                        FragmentIon(Fragment('b', 5, "", '', [], 0), 1, [], 0),
                        FragmentIon(Fragment('b', 5, "-G", '', [], 0), 1, [], 0)]"""
    """def fill(pattern, flag):
        for i, ion in enumerate(pattern):
            ion.intensity = 3 * 10 ** 6 * (i + 1) + i * 100
            ion.error = i + 0.01
            ion.quality = 0.5 - i / 100
            ion.noise = 10 ** 6 * 2
            if flag == 1:
                ion.comment = 'del.'
        return pattern

    ions, delIons = [],[]
    for name in ['a','c', 'w','y']:
        for nr in range(1,20):
            ions.append(FragmentIon(Fragment(name, nr, "", '', [], 0), 1, [], 0))
            delIons.append(FragmentIon(Fragment(name, nr, "-G", '', [], 0), 1, [], 0))
    ions = fill(ions,0)

    delIons = fill(delIons,1)

    app=QtWidgets.QApplication(sys.argv)
    window=ResultsWindow({(ion.getName(),ion.charge): ion for ion in ions},
                      {(ion.getName(),ion.charge): ion for ion in delIons}, [],[])"""
    peaks = [(1527.24157, 1, 4649010, 'y05', -2.1067545, 1), (1528.24749953, 1, 2777892, 'y05', 0.0, 1),(1529.24749953, 1, 2777892, 'y05', 0.0, 1)]

    app = QtWidgets.QApplication([])
    peakview = PeakView(None, peaks)
    #peakview.show()
    app.exec_()