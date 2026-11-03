from math import isnan

from PySide6 import QtWidgets
from PySide6.QtCore import Qt

from src.gui.GUI_functions import setWindowIcon, translate
from src.gui.tableviews.TableModels import AbstractTableModel
from src.gui.tableviews.TableViews import TableView


class PlotTableModel(AbstractTableModel):
    '''
    TableModel for QTableView in PlotTableView for occupancies, average charges,...
    '''
    def __init__(self, data, keys, precision):
        self._ionTypes = len(keys)
        #print(data, '\n', data[0][len(data)-1])
        valFormat = '{:2.'+str(precision)+'f}'
        format = ['','{:2d}'] + self._ionTypes * [valFormat] + ['{:2d}', '', ]
        headers = ['sequ. (f)','cleav. side (f)'] + keys + ['cleav. side (b)','sequ. (b)']
        super(PlotTableModel, self).__init__(data,format, headers)

    def data(self, index, role):
        '''
        Overwrites the data method of AbstractTableModel to correctly format each value
        '''
        if index.isValid():
            if role == Qt.ItemDataRole.DisplayRole:
                col = index.column()
                item = self._data[index.row()][col]
                if col == 0 or col == len(self._data[0])-1:
                    return item
                #print(item)
                elif isnan(item):
                    return ''
                return self._format[col].format(item)
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignRight


class PlotTableView(QtWidgets.QWidget):
    '''
    Widget with QTableView showing occupancies, av. charges, ... of each fragment
    '''
    def __init__(self, parent, data, keys, title, precision, firstLine = None):
        super().__init__(parent)
        verticalLayout = QtWidgets.QVBoxLayout(self)
        self._translate = translate
        if firstLine is not None:
            horizontalWidget = QtWidgets.QWidget(self)
            formLayout = QtWidgets.QFormLayout(horizontalWidget)
            label = QtWidgets.QLabel(horizontalWidget)
            label.setText(self._translate(self.objectName(), '% modified precursor ions:'))
            formLayout.setWidget(0, QtWidgets.QFormLayout.ItemRole.LabelRole, label)
            valLabel = QtWidgets.QLabel(horizontalWidget)
            valLabel.setText(self._translate(self.objectName(), str(round(firstLine*100,1))+' %'))
            valLabel.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
            formLayout.setWidget(0, QtWidgets.QFormLayout.ItemRole.FieldRole, valLabel)
            verticalLayout.addWidget(horizontalWidget)
        scrollArea = QtWidgets.QScrollArea(self)
        scrollArea.setWidgetResizable(True)
        self._table = TableView(self, PlotTableModel(data, keys,precision))
        scrollArea.setWidget(self._table)
        self.setObjectName(title)
        self.setWindowTitle(self._translate(self.objectName(), self.objectName()))
        self._table.resizeColumnsToContents()
        self._table.resizeRowsToContents()
        verticalLayout.addWidget(scrollArea)
        setWindowIcon(self)
        self.show()

    def sortBy(self, columnIndex):
        self._table.sortByColumn(columnIndex, Qt.SortOrder.AscendingOrder)