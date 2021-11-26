from PyQt5 import QtWidgets
import pyqtgraph as pg
import numpy as np

from src.gui.GUI_functions import translate, showOptions
from src.gui.tableviews.TableModels import CalibrationInfoTable2, CalibrationInfoTable1
from src.gui.tableviews.TableViews import TableView
from src.gui.widgets.IonTableWidgets import CalibrationIonTableWidget


class CalibrationView(QtWidgets.QDialog):
    '''
    Dialog for controlling calibration
    '''
    def __init__(self, calibrator):
        super(CalibrationView, self).__init__()
        self._calibrator = calibrator
        self._canceled = False
        self._layout = QtWidgets.QVBoxLayout(self)
        self.fillUI()

    def fillUI(self):
        self.setWindowTitle(translate(self.objectName(), 'Calibration'))
        self._widgets = []
        upperWidget = QtWidgets.QWidget(self)
        upperWidgetLayout = QtWidgets.QHBoxLayout(upperWidget)
        calVals, qualityVals = self.getData()
        self._table1a = self.makeCalTable(calVals, upperWidget, 'Values of calibration function: m/z_cal = a * (m/z)^2 * b * m/z + c')
        upperWidgetLayout.addWidget(self._table1a)
        self._table1b = self.makeCalTable(qualityVals, upperWidget, 'quality of the calibration')
        upperWidgetLayout.addWidget(self._table1b)
        self.addWidget(upperWidget)
        self.plot()
        scrollArea = QtWidgets.QScrollArea(self)
        scrollArea.setWidgetResizable(True)
        self._table2 = CalibrationIonTableWidget(scrollArea, self._ionsVals)
        scrollArea.setWidget(self._table2)
        #connectTable(self._table2, showOptions)
        self.addWidget(scrollArea)
        self.addWidget(self.makeButtonBox())
        #self._table2.viewport().installEventFilter(self)


    def addWidget(self, widget):
        self._layout.addWidget(widget)
        self._widgets.append(widget)


    def getData(self):
        quality = self._calibrator.getQuality()
        self._ionsVals = np.sort(self._calibrator.getIonArray(), order=['m/z'])
        self._solution, errors = self._calibrator.getCalibrationValues()
        calVals = []
        for i, key in enumerate(['a', 'b', 'c']):
            calVals.append((key, self._solution[i], errors[i]))
        qualityVals = []
        for i, key in enumerate(['av.error', 'std.dev.']):
            qualityVals.append((key, quality[i]))
        return calVals, qualityVals

    def makeCalTable(self, data, parent, toolTip):
        if len(data[0])==2:
            model = CalibrationInfoTable1(data, '{:1.2}')
        else:
            model = CalibrationInfoTable2(data, '{:2.6}')
        '''table = QtWidgets.QTableView(parent)
        table.setSortingEnabled(True)
        table.setModel(model)
        table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        table.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)'''
        table = TableView(parent, model)
        table.resizeRowsToContents()
        #connectTable(table, self.showOptions)
        table.setToolTip(toolTip)
        return table


    def plot(self):
        self._plot1 = pg.plot()
        #self._plot1.addLegend(labelTextSize='14pt')
        self._plot1.setBackground('w')
        styles = {"black": "#f00", "font-size": "14px"}
        self._plot1.setLabel('bottom', 'm/z (observed)', **styles)
        self._plot1.setLabel('left', 'delta', **styles)
        usedIons = self._ionsVals[self._ionsVals['used']==True]
        scatter = pg.ScatterPlotItem(x=usedIons['m/z'], y=usedIons['m/z']-usedIons['m/z_theo'], symbol='star',
                                     pen=pg.mkPen(color='g', width=2),
                                     brush=(0, 0, 0, 0), size=10, pxMode=True)
        xVals = np.linspace(int(np.min(self._ionsVals['m/z']))-100, int(np.max(self._ionsVals['m/z']))+100, 1000)
        yVals = [-(self._solution[0]*x**2+(self._solution[1]-1)*x+self._solution[2]) for x in xVals]
        curve = pg.PlotCurveItem(x=xVals, y=yVals, pen=pg.mkPen(color='k', width=1))
        self._plot1.addItem(scatter)
        self._plot1.addItem(curve)
        self.addWidget(self._plot1)


    def makeButtonBox(self):
        btnWidget = QtWidgets.QWidget(self)
        hLayout = QtWidgets.QHBoxLayout(btnWidget)
        hLayout.addWidget(self.makeBtn(btnWidget, "Update", self.update))
        hLayout.addWidget(self.makeBtn(btnWidget, "Cancel", self.reject))
        hLayout.addWidget(self.makeBtn(btnWidget, "Ok", self.accept))
        return btnWidget


    def makeBtn(self, parent, text, fun):
        btn = QtWidgets.QPushButton(parent)
        btn.setText(translate(self.objectName(), text))
        btn.clicked.connect(fun)
        return btn

    def update(self):
        ions = [(row[0],row[1]) for row in self._table2.checkStatus() if row[2]]
        self._calibrator.recalibrate(ions)
        for widget in self._widgets:
            self._layout.removeWidget(widget)
            del widget
        self.fillUI()


    def reject(self):
        self._canceled = True
        super(CalibrationView, self).reject()


    def canceled(self):
        return self._canceled

    '''def showOptions(self, table, pos):
        menu = QtWidgets.QMenu()
        copyAllAction = menu.addAction("Copy Table")
        copyAction = menu.addAction("Copy Cell")
        action = menu.exec_(table.viewport().mapToGlobal(pos))
        if table == self._table2:
            df = pd.DataFrame(data = table.getData(), columns=table.getHeaders())
        else:
            df = pd.DataFrame(data=table.model().getData(), columns=table.model().getHeaders())
        df.to_clipboard(index=False, header=True)
        if action == copyAction:
            it = table.indexAt(pos)
            if it is None:
                return
            selectedRow = it.row()
            selectedCol = it.column()
            if table == self._table2:
                df = pd.DataFrame(data = [table.getData()[selectedRow][selectedCol]])
            else:
                df = pd.DataFrame(data=[table.model().getData()[selectedRow][selectedCol]])
            df.to_clipboard(index=False, header=True)
        elif action == copyAllAction:
            if table == self._table2:
                df = pd.DataFrame(data = table.getData(), columns=table.getHeaders())
            else:
                df = pd.DataFrame(data=table.model().getData(), columns=table.model().getHeaders())
            df.to_clipboard(index=False, header=True)'''
