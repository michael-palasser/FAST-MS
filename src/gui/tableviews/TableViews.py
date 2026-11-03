from PySide6 import QtWidgets, QtCore

from src.gui.GUI_functions import connectTable, showOptions


class TableView(QtWidgets.QTableView):
    '''
    QTableView with rightclick-menu
    '''
    def __init__(self, parent, model, optionFun=showOptions, sort=None):
        super(TableView, self).__init__(parent)
        self.setModel(model)
        self.setSortingEnabled(True)
        self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        connectTable(self, optionFun)
        if sort is not None:
            self.sortByColumn(sort, QtCore.Qt.SortOrder.AscendingOrder)