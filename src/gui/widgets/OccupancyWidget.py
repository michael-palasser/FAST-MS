from PyQt5 import QtWidgets
from PyQt5 import QtCore

from src.gui.tableviews.PlotTables import PlotTableView


class OccupancyWidget(QtWidgets.QWidget):
    '''
    Widget with QTableView showing relative percentages of each fragment
    '''
    def __init__(self,modification, percData,percHeaders, modificationLoss, absData, absHeaders):
        super().__init__(parent=None)
        verticalLayout = QtWidgets.QVBoxLayout(self)
        self.setWindowTitle('Occupancies')
        #scrollArea = QtWidgets.QScrollArea(self)
        #_scrollArea.setGeometry(QtCore.QRect(10, 10, len(typeData[0])*50+200, len(typeData)*22+25))
        #scrollArea.setWidgetResizable(True)
        # _scrollArea.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        # _scrollArea.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        table1 = PlotTableView(percData, percHeaders, 'Occupancies: ' + modification, 3,
                               modificationLoss)
        verticalLayout.addWidget(table1)
        '''self._table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self._table.customContextMenuRequested['QPoint'].connect(partial(self.showOptions, self._table))'''
        #scrollArea.setWidget(table1)
        #self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        #self._table.move(0,0)

        table2 = PlotTableView(absData, absHeaders, 'Abs. Occupancies: ' + modification, 1)
        verticalLayout.addWidget(table2)
        self.show()
        #self.setObjectName('Occupancioes')
        #self._translate = QtCore.QCoreApplication.translate
