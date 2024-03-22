from PyQt5 import QtWidgets

from src.gui.GUI_functions import setIcon
from src.gui.tableviews.PlotTables import PlotTableView


class OccupancyWidget(QtWidgets.QWidget):
    '''
    Widget with a QTableView showing relative percentages of each fragment and a second QTableView showing sums of the
     relative abundances of each fragment (unmodified/modified)
    '''
    def __init__(self,modification, percData,percHeaders, modificationLoss, absData, absHeaders):
        super().__init__(parent=None)
        verticalLayout = QtWidgets.QVBoxLayout(self)
        self.setWindowTitle('Localise '+modification)
        #scrollArea = QtWidgets.QScrollArea(self)
        #_scrollArea.setGeometry(QtCore.QRect(10, 10, len(typeData[0])*50+200, len(typeData)*22+25))
        #scrollArea.setWidgetResizable(True)
        # _scrollArea.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        # _scrollArea.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        table1 = PlotTableView(None, percData, percHeaders, 'Localise: ' + modification, 3,
                               modificationLoss)
        table1.sortBy(1)
        verticalLayout.addWidget(table1)
        '''self._table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self._table.customContextMenuRequested['QPoint'].connect(partial(self.showOptions, self._table))'''
        #scrollArea.setWidget(table1)
        #self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        #self._table.move(0,0)

        table2 = PlotTableView(None, absData, absHeaders, 'Rel. Abundances: ' + modification, 1)
        table2.sortBy(1)
        verticalLayout.addWidget(table2)
        setIcon(self)
        self.show()
        #self.setObjectName('Occupancioes')
        #self._translate = QtCore.QCoreApplication.translate
