
from math import log10
from PyQt5 import QtCore, QtGui
from src.gui.tableviews.TableModels import AbstractTableModel

class MD_BestIonsTableModel(AbstractTableModel):
    '''
    TableModel for QTableView presenting ion values (in top-down search)
    '''
    def __init__(self, data, precRegion):
        headers = ('cl. site','m/z','z','intensity','name','error /ppm', 'S/N','quality', 'comment',
            'I (SNAP)', 'S/N (SNAP)', 'quality (SNAP)', 'I (Sum Peak)', 'S/N (Sum Peak)', 'final score')
        if len(data)==0:
            data=[['' for _ in headers]]
        
        super(MD_BestIonsTableModel, self).__init__(data, ('{:2d}','{:10.4f}','{:2d}', '{:12d}', '','{:4.2f}', '{:6.1f}', '{:4.2f}',
               '', '{:12d}', '{:6.1f}', '{:4.2f}', '{:12d}', '{:6.1f}', '{:4.2f}'), headers)
        self._precRegion = precRegion

    def data(self, index, role):
        '''
        Overwrites the data method of AbstractTableModel to correctly format each value
        '''
        if index.isValid():
            if role == QtCore.Qt.DisplayRole:
                if self._data[0][0] == '':
                    return ''
                col = index.column()
                item = self._data[index.row()][col]
                formatString = self._format[col]
                if item =="":
                    return item
                if (col == 4) or (col == 8):
                    return item
                if col in (3,9,12) :
                    if item >= 10 ** 13:
                        lg10 = str(int(log10(item) + 1))
                        formatString = '{:' + lg10 + 'd}'
                    return formatString.format(item)
                return formatString.format(item)
        if role == QtCore.Qt.TextAlignmentRole:
            if index.column() in (3,6,9,12):
                return QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
            else:
                return QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
        if role == QtCore.Qt.FontRole:
            if index.column() == 8:
                font = QtGui.QFont()
                font.setPointSize(10)
                return font
        if role == QtCore.Qt.ForegroundRole:
            col = index.column()
            item = self._data[index.row()][col]
            if item == '':
                return QtGui.QColor('k')
            if (col == 1) and (self._precRegion is not None):
                if self._precRegion[0]<item<self._precRegion[1]:
                    return QtGui.QColor('red')

    def getHashOfRow(self, rowIndex):
        return (self._data[rowIndex][4],self._data[rowIndex][2])

    def getRow(self, rowIndex):
        return self._data[rowIndex]

    def exchangeIon(self, index, newRow):
        self._data[index] = newRow

    """def setData(self, newData):
        if len(newData)==0:
            newData = ['' for _ in self._headers]
        super(MD_BestIonsTableModel, self).setData(newData)"""

    def updateData(self, newRow):
        for i, row in enumerate(self._data):
            if row[0]==newRow[0]:
                self._data[i] = newRow
                self.layoutChanged.emit()
                #self.dataChanged.emit(i,i)
                break
    
    def getSNs(self):
        return [(vals[10],vals[13]) for vals in self._data]
                


    """def addData(self, newRow):
        if self._data[0][0] == '':
            del self._data[0]
        dataLength = len(self._data)
        self.beginInsertRows(QtCore.QModelIndex(),dataLength, dataLength)
        self._data.append(newRow)
        self.endInsertRows()

    

    def removeByIndex(self, indexToRemove):
        self.beginRemoveRows(QtCore.QModelIndex(), indexToRemove, indexToRemove)
        del self._data[indexToRemove]
        self.endRemoveRows()
        if len(self._data)==0:
            self._data.append(['' for _ in self._headers])"""


"""class MD_Evaluation(AbstractTableModel):
    '''
    TableModel for QTableView presenting ion values (in top-down search)
    '''
    def __init__(self, data):
        super(MD_Evaluation, self).__init__(data, ('{:6.1f}', '{:6.1f}','{:6.1f}'), ('Minimum','1. Quartile','Median'))

    def exchangeData(self, newData):
        self._data = newData
        self.layoutChanged.emit()"""