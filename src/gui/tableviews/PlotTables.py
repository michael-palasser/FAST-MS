from math import isnan

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt

from src.gui.GUI_functions import setIcon
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
        headers = ['Sequ. (f)','Cleav. Side (f)'] + keys + ['Cleav. Side (b)','Sequ. (b)']
        super(PlotTableModel, self).__init__(data,format, headers)

    def data(self, index, role):
        '''
        Overwrites the data method of AbstractTableModel to correctly format each value
        '''
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
        if role == Qt.TextAlignmentRole:
            return Qt.AlignRight


class PlotTableView(QtWidgets.QWidget):
    '''
    Widget with QTableView showing occupancies, av. charges, ... of each fragment
    '''
    def __init__(self, parent, data, keys, title, precision, firstLine = None):
        super().__init__(parent)
        verticalLayout = QtWidgets.QVBoxLayout(self)
        self._translate = QtCore.QCoreApplication.translate
        if firstLine is not None:
            horizontalWidget = QtWidgets.QWidget(self)
            formLayout = QtWidgets.QFormLayout(horizontalWidget)
            label = QtWidgets.QLabel(horizontalWidget)
            label.setText(self._translate(self.objectName(), 'Prec. Mod. Loss:'))
            formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, label)
            valLabel = QtWidgets.QLabel(horizontalWidget)
            valLabel.setText(self._translate(self.objectName(), str(round(firstLine*100,1))+' %'))
            valLabel.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse | QtCore.Qt.TextSelectableByKeyboard)
            formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, valLabel)
            verticalLayout.addWidget(horizontalWidget)
        scrollArea = QtWidgets.QScrollArea(self)
        #_scrollArea.setGeometry(QtCore.QRect(10, 10, len(data[0])*50+200, len(data)*22+25))
        scrollArea.setWidgetResizable(True)
        # _scrollArea.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        # _scrollArea.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self._table = TableView(self, PlotTableModel(data, keys,precision))
        """model = PlotTableModel(data, keys,precision)
        self._table = QtWidgets.QTableView(self)
        self._table.setSortingEnabled(True)
        self._table.setModel(model)
        self._table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self._table.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        #self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        connectTable(self._table,showOptions)"""
        '''self._table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self._table.customContextMenuRequested['QPoint'].connect(partial(self.showOptions, self._table))'''
        scrollArea.setWidget(self._table)
        #self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        #self._table.move(0,0)
        self.setObjectName(title)
        self.setWindowTitle(self._translate(self.objectName(), self.objectName()))
        self._table.resizeColumnsToContents()
        self._table.resizeRowsToContents()
        verticalLayout.addWidget(scrollArea)
        #self.resize(len(data[0])*50+200, len(data)*22+25)
        setIcon(self)
        self.show()

    def sortBy(self, columnIndex):
        self._table.sortByColumn(columnIndex, Qt.AscendingOrder)

    '''def showOptions(self, table, pos):
        menu = QtWidgets.QMenu()
        copyAction = menu.addAction("Copy Table")
        action = menu.exec_(table.viewport().mapToGlobal(pos))
        if action == copyAction:
            df=pd.DataFrame(data=self._table.model().getData(), columns=self._table.model().getHeaders())
            df.to_clipboard(index=False,header=True)'''