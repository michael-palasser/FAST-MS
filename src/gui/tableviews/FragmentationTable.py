
from PyQt5 import QtCore, QtWidgets


from src.gui.GUI_functions import connectTable, showOptions
from src.gui.tableviews.TableModels import AbstractTableModel


class FragmentationTableModel(AbstractTableModel):
    '''
    TableModel for QTableView in FragmentationTable which shows the relative percentages of each fragment
    '''
    def __init__(self, data):
        super(FragmentationTableModel, self).__init__(data, ('','{:1.3f}'),
                         ('type', 'rel.proportion'))
        self._data = data

    def data(self, index, role):
        '''
        Overwrites the data method of AbstractTableModel to correctly format each value
        '''
        if index.isValid():
            if role == QtCore.Qt.DisplayRole:
                col = index.column()
                item = self._data[index.row()][col]
                formatString = self._format[col]
                if col == 0:
                    return item
                else:
                    return formatString.format(item)
        if role == QtCore.Qt.TextAlignmentRole:
            return QtCore.Qt.AlignCenter


class FragmentationTable(QtWidgets.QWidget):
    '''
    Widget with QTableView showing relative percentages of each fragment
    '''
    def __init__(self, data):
        super().__init__(parent=None)
        verticalLayout = QtWidgets.QVBoxLayout(self)
        scrollArea = QtWidgets.QScrollArea(self)
        #_scrollArea.setGeometry(QtCore.QRect(10, 10, len(data[0])*50+200, len(data)*22+25))
        scrollArea.setWidgetResizable(True)
        # _scrollArea.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        # _scrollArea.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        model = FragmentationTableModel(data)
        self._table = QtWidgets.QTableView(self)
        self._table.setSortingEnabled(True)
        self._table.setModel(model)
        self._table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self._table.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        #self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        connectTable(self._table, showOptions)
        '''self._table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self._table.customContextMenuRequested['QPoint'].connect(partial(self.showOptions, self._table))'''
        scrollArea.setWidget(self._table)
        #self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        #self._table.move(0,0)
        self.setObjectName('Fragmentation Efficiencies')
        self._translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(self._translate(self.objectName(), self.objectName()))
        self._table.resizeColumnsToContents()
        self._table.resizeRowsToContents()
        verticalLayout.addWidget(scrollArea)
        #self.resize(len(data[0])*50+200, len(data)*22+25)
        self.show()

