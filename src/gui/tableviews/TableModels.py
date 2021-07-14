from math import log10

'''try:
    from Tkinter import Tk
except ImportError:
    from tkinter import Tk'''
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import Qt


class AbstractTableModel(QtCore.QAbstractTableModel):
    '''
    QAbstractTableModel which is the basis for all QTableViews in the program.
    Superclass of IonTableModel, PeakTableModel, and PlotTableModel
    '''
    def __init__(self, data, format, headers):
        super(AbstractTableModel, self).__init__()
        self._data = data
        self._format = format
        self._headers = headers

    def data(self, index, role):
        '''
        Overwrites the data method of QAbstractTableModel to correctly format each value
        '''
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
        """
        Sort table by selected column
        """
        self.layoutAboutToBeChanged.emit()
        #self._data = self._data.sort_values(self._headers[Ncol], ascending=order == Qt.AscendingOrder)
        if order == Qt.AscendingOrder:
            #self._data.sort(key= lambda tup:tup[Ncol])
            self._data = sorted(self._data, key= lambda tup:tup[Ncol])
        else:
            #self._data.sort(key= lambda tup:tup[Ncol], reverse=True)
            self._data = sorted(self._data,key= lambda tup:tup[Ncol], reverse=True)
        self.layoutChanged.emit()


class IonTableModel(AbstractTableModel):
    '''
    TableModel for QTableView presenting ion values (in top-down search)
    '''
    def __init__(self, data, precRegion, maxQual, maxScore):
        super(IonTableModel, self).__init__(data, ('{:10.5f}','{:2d}', '{:12d}', '','{:4.2f}', '{:6.1f}', '{:4.2f}',
               '{:4.1f}', ''), ('m/z','z','intensity','fragment','error /ppm', 'S/N','quality', 'score', 'comment'))
        self._precRegion = precRegion
        self._maxQual = maxQual
        self._maxScore = maxScore

    """def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable"""

    def data(self, index, role):
        '''
        Overwrites the data method of AbstractTableModel to correctly format each value
        '''
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

    def updateData(self, newRow):
        for i, row in enumerate(self._data):
            if row[1]==newRow[1] and row[3]==newRow[3]:
                self._data[i] = newRow
                break


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
        '''
        Overwrites the data method of AbstractTableModel to correctly format each value
        '''
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