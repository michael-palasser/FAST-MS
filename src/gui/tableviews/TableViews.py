from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt

from src.gui.GUI_functions import connectTable, showOptions


class TableView(QtWidgets.QTableView):
    '''
    QTableView with rightclick-menu
    '''
    def __init__(self, parent, model, optionFun=showOptions, sort=None):
        super(TableView, self).__init__(parent)
        self.setModel(model)
        self.setSortingEnabled(True)
        self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        connectTable(self, optionFun)
        if sort is not None:
            self.sortByColumn(sort, Qt.AscendingOrder)