
from PySide6 import QtWidgets
from PySide6.QtCore import Qt

from src.gui.GUI_functions import setWindowIcon, translate
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
            if role == Qt.ItemDataRole.DisplayRole:
                col = index.column()
                item = self._data[index.row()][col]
                formatString = self._format[col]
                if col == 0:
                    return item
                else:
                    return formatString.format(item)
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignCenter


class FragmentationTable(QtWidgets.QWidget):
    '''
    Widget with QTableView showing relative percentages of each fragment
    '''
    def __init__(self, typeData, siteData, siteHeaders, title):
        super().__init__(parent=None)
        verticalLayout = QtWidgets.QVBoxLayout(self)
        self._table = TableView(self, FragmentationTableModel(typeData))
        self._table.sortByColumn(0, Qt.SortOrder.AscendingOrder)

        self.setObjectName(title)
        self._translate = translate
        self.setWindowTitle(self._translate(self.objectName(), self.objectName()))
        self._table.resizeColumnsToContents()
        self._table.resizeRowsToContents()
        verticalLayout.addWidget(self._table)
        table2 = PlotTableView(None, siteData, siteHeaders,'Fragmentation Efficiencies: ',0)
        table2.sortBy(1)
        verticalLayout.addWidget(table2)
        setWindowIcon(self)
        self.show()

