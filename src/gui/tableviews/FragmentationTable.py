
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt

from src.gui.GUI_functions import setIcon, translate
from src.gui.tableviews.PlotTables import PlotTableView
from src.gui.tableviews.TableModels import AbstractTableModel
from src.gui.tableviews.TableViews import TableView


class FragmentationTableModel(AbstractTableModel):
    '''
    TableModel for QTableView in FragmentationTable which shows the relative percentages of each fragment
    '''
    def __init__(self, data):
        super(FragmentationTableModel, self).__init__(data, ('','{:1.3f}'), ('type', 'yield'))
        self._data = data

    def data(self, index, role):
        '''
        Overwrites the typeData method of AbstractTableModel to correctly format each value
        '''
        if index.isValid():
            if role == Qt.DisplayRole:
                col = index.column()
                item = self._data[index.row()][col]
                formatString = self._format[col]
                if col == 0:
                    return item
                else:
                    return formatString.format(item)
        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter


class FragmentationTable(QtWidgets.QWidget):
    '''
    Widget with QTableView showing relative percentages of each fragment
    '''
    def __init__(self, typeData, siteData, siteHeaders):
        super().__init__(parent=None)
        verticalLayout = QtWidgets.QVBoxLayout(self)
        #scrollArea = QtWidgets.QScrollArea(self)
        #_scrollArea.setGeometry(QtCore.QRect(10, 10, len(typeData[0])*50+200, len(typeData)*22+25))
        #scrollArea.setWidgetResizable(True)
        # _scrollArea.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        # _scrollArea.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self._table = TableView(self, FragmentationTableModel(typeData))
        self._table.sortByColumn(0, Qt.AscendingOrder)
        """model = FragmentationTableModel(typeData)
        self._table = QtWidgets.QTableView(self)
        self._table.setSortingEnabled(True)
        self._table.setModel(model)
        self._table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self._table.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        #self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        connectTable(self._table, showOptions)"""
        '''self._table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self._table.customContextMenuRequested['QPoint'].connect(partial(self.showOptions, self._table))'''

        #scrollArea.setWidget(self._table)

        #self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        #self._table.move(0,0)
        self.setObjectName('Fragmentation Efficiencies')
        self._translate = translate
        self.setWindowTitle(self._translate(self.objectName(), self.objectName()))
        self._table.resizeColumnsToContents()
        self._table.resizeRowsToContents()
        #verticalLayout.addWidget(scrollArea)
        verticalLayout.addWidget(self._table)
        #self.resize(len(typeData[0])*50+200, len(typeData)*22+25)
        table2 = PlotTableView(None, siteData, siteHeaders,'Fragmentation Efficiencies: ',0)
        #table2.setContentsMargins(0,0,0,0)
        table2.sortBy(1)
        verticalLayout.addWidget(table2)
        setIcon(self)
        self.show()

