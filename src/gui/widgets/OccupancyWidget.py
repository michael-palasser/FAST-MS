from PySide6 import QtWidgets

from src.gui.GUI_functions import setWindowIcon
from src.gui.tableviews.PlotTables import PlotTableView


class OccupancyWidget(QtWidgets.QWidget):
    '''
    Widget with a QTableView showing relative percentages of each fragment and a second QTableView showing sums of the
     relative abundances of each fragment (unmodified/modified)
    '''
    def __init__(self,modification, percData,percHeaders, modificationLoss, absData, absHeaders, title):
        super().__init__(parent=None)
        verticalLayout = QtWidgets.QVBoxLayout(self)
        self.setWindowTitle(title)
        table1 = PlotTableView(None, percData, percHeaders, 'Localise: ' + modification, 3,
                               modificationLoss)
        table1.sortBy(1)
        verticalLayout.addWidget(table1)
        table2 = PlotTableView(None, absData, absHeaders, 'Rel. Abundances: ' + modification, 1)
        table2.sortBy(1)
        verticalLayout.addWidget(table2)
        setWindowIcon(self)
        self.show()
