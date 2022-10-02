import copy

from PyQt5 import QtWidgets

from src.gui.GUI_functions import connectTable, showOptions, setIcon, translate
from src.gui.tableviews.TableViews import TableView
from src.gui.widgets.IonTableWidgets import IonTableWidget
from src.gui.widgets.PeakWidgets import PeakWidget
from src.gui.tableviews.TableModels import PeakTableModel


class SimplePeakView(QtWidgets.QWidget):
    '''
    Widget with QTableView showing original peak values of remodelled ions
    '''
    def __init__(self, parent, ion):
        super().__init__(parent)
        self._peaks = ion.getIsotopePattern()
        # self.proxyModel = QSortFilterProxyModel()
        # self.proxyModel.setSourceModel(_model)
        layout = QtWidgets.QVBoxLayout(self)
        self._table = TableView(self, PeakTableModel(self._peaks))
        """
        model = PeakTableModel(self._peaks)
        self._table = QtWidgets.QTableView(self)
        self._table.setSortingEnabled(True)
        self._table.setModel(model)
        self._table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self._table.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        # self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        connectTable(self._table,self.showOptions)"""
        #self._table.customContextMenuRequested['QPoint'].connect(partial(self.showOptions, self._table))
        # self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        # self._table.move(0,0)
        #title = peaks[0][3] + ', ' + str(peaks[0][1])
        self.setObjectName(ion.getId())
        self._translate = translate
        self.setWindowTitle(self._translate(self.objectName(), self.objectName()))
        layout.addWidget(self._table)
        #self.resize(650, (len(self._peaks)) * 38 + 30)
        setIcon(self)
        self.show()

    """def showOptions(self, table, pos):
        menu = QtWidgets.QMenu()
        copyAllAction = menu.addAction("Copy Table")
        copyAction = menu.addAction("Copy Cell")
        action = menu.exec_(table.viewport().mapToGlobal(pos))
        if action == copyAllAction:
            data = [[str(val) for val in row] for row in self._peaks]
            df=pd.DataFrame(data=data, columns=table.model().getHeaders())
            df.to_clipboard(index=False,header=True)
        if action == copyAction:
            it = table.indexAt(pos)
            if it is None:
                return
            selectedRow = it.row()
            selectedCol = it.column()
            df = pd.DataFrame([self._peaks[selectedRow][selectedCol]])
            df.to_clipboard(index=False, header=False)"""


class PeakView(QtWidgets.QMainWindow):
    '''
    Window which is used in top-down search. It pops up when a user right-clicks on an ion in the table.
    User can then view the peak values, manually change intensities in the spectrum and re-model the ion intensity.
    '''
    def __init__(self, parent, ion, model, save):
        super(PeakView, self).__init__(parent)
        self._ion = copy.deepcopy(ion)
        self._translate = translate
        self.setWindowTitle(self._translate(self.objectName(), ion.getName()+', '+str(ion.getCharge())))
        #self.centralwidget = QtWidgets.QWidget(self)
        self.setCentralWidget(QtWidgets.QWidget(self))
        self._verticalLayout = QtWidgets.QVBoxLayout(self.centralWidget())
        self._ionTable = IonTableWidget(self.centralWidget(),(self._ion,),30)
        self._peakTable = PeakWidget(self.centralWidget(), self._ion.getIsotopePattern())
        self._model = model
        self._save = save
        buttonWidget = QtWidgets.QWidget(self.centralWidget())
        horizontalLayout = QtWidgets.QHBoxLayout(buttonWidget)
        horizontalLayout.addWidget(self.makeBtn(buttonWidget,'Model',
                                'Model isotope distribution to peaks in spectrum', self.modelIon))
        horizontalLayout.addWidget(self.makeBtn(buttonWidget,'Save',
                                'Replaces old values with newly calculated ones', self.saveIon))
        #horizontalLayout.addWidget(self.makeIntensityWidget(self.centralWidget()))
        horizontalLayout.addItem(QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        self._verticalLayout.addWidget(buttonWidget)

        self._verticalLayout.addWidget(self._ionTable)
        self._verticalLayout.addWidget(self._peakTable)

        connectTable(self._ionTable,showOptions)
        '''self._ionTable.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self._ionTable.customContextMenuRequested['QPoint'].connect(partial(self.showOptions, self._ionTable))'''

        self.show()

    @staticmethod
    def makeBtn(parent, text, toolTip, fun):
        btn = QtWidgets.QPushButton(parent)
        btn.setText(text)
        btn.setToolTip(toolTip)
        btn.clicked.connect(fun)
        return btn

    def makeIntensityWidget(self, parent):
        widget = QtWidgets.QWidget(parent)
        horizontalLayout = QtWidgets.QHBoxLayout(widget)
        label = QtWidgets.QLabel(widget)
        label.setText(self._translate(self.objectName(), 'Int:'))
        horizontalLayout.addWidget(label)
        self._intInfo = QtWidgets.QLabel(widget)
        self._intInfo.setText(self._translate(self.objectName(), str(self._ion.getIntensity())))
        horizontalLayout.addWidget(self._intInfo)
        return widget


    def modelIon(self):
        vals = self._peakTable.readTable()
        newIon = self._model(copy.deepcopy(self._ion), vals)
        if self._ion.getIntensity() != newIon.getIntensity():
            self._ion = newIon
            self._peakTable.setPeaks(self._ion.getIsotopePattern())
            self._verticalLayout.removeWidget(self._ionTable)
            del self._ionTable
            self._ionTable =  IonTableWidget(self.centralWidget(),(self._ion,),30)
            self._verticalLayout.insertWidget(1, self._ionTable)
            #self._intInfo.setText(self._translate(self.objectName(), str(self._ion.getIntensity())))

    def saveIon(self):
        self._save(self._ion)

    '''def showOptions(self, table, pos):
        menu = QtWidgets.QMenu()
        copyAllAction = menu.addAction("Copy Table")
        copyAction = menu.addAction("Copy Cell")
        action = menu.exec_(table.viewport().mapToGlobal(pos))
        if action == copyAction:
            it = table.indexAt(pos)
            if it is None:
                return
            selectedCol = it.column()
            df = pd.DataFrame([self._ion.getValues()[selectedCol]])
            df.to_clipboard(index=False, header=False)
        if action == copyAllAction:
            df = pd.DataFrame(data=[self._ion.getValues()], columns=table.getHeaders())
            df.to_clipboard(index=False, header=True)'''