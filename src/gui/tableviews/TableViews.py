from PyQt5 import QtWidgets

from src.gui.GUI_functions import connectTable, showOptions


class TableView(QtWidgets.QTableView):
    '''
    QTableView with rightclick-menu
    '''
    def __init__(self, parent, model, optionFun=showOptions):
        super(TableView, self).__init__(parent)
        self.setModel(model)
        self.setSortingEnabled(True)
        self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        connectTable(self, optionFun)