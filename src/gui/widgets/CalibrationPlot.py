from PyQt5 import QtWidgets
import pyqtgraph as pg
import numpy as np

from src.gui.GUI_functions import translate
from src.gui.tableviews.TableModels import CalibrationInfoTable
from src.gui.widgets.IonTableWidgets import CalibrationIonTableWidget


class CalibrationPlot(QtWidgets.QDialog):
    def __init__(self, parent, quality, ionsVals, solution, errors):
        super(CalibrationPlot, self).__init__(parent)
        self._quality = quality
        self._ionsVals = ionsVals
        self._solution = solution
        self._errors = errors
        self._layout = QtWidgets.QVBoxLayout(self)
        calVals = []
        for i,key in enumerate(['a','b','c']):
            calVals.append((key, solution[i],errors[i]))
        model = CalibrationInfoTable(calVals)
        table1 = QtWidgets.QTableView(self)
        table1.setSortingEnabled(True)
        table1.setModel(model)
        table1.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        table1.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        #connectTable(table1,self.showOptions)
        self._layout.addWidget(table1)
        self.plot()
        scrollArea = QtWidgets.QScrollArea(self)
        scrollArea.setWidgetResizable(True)
        table2 = CalibrationIonTableWidget(scrollArea, self._ionsVals)
        #connectTable(table2,self.showOptions)
        scrollArea.setWidget(table2)
        self._layout.addWidget(scrollArea)
        self._layout.addWidget(self.makeButtonBox())



    def plot(self):
        self._plot1 = pg.plot()
        self._plot1.addLegend(labelTextSize='14pt')
        self._plot1.setBackground('w')
        print(self._ionsVals, self._ionsVals.dtype)
        usedIons = self._ionsVals[self._ionsVals['used']==True]
        scatter = pg.ScatterPlotItem(x=usedIons['m/z'], y=usedIons['m/z']-usedIons['m/z_theo'], symbol='star',
                                     pen=pg.mkPen(color='g', width=2),
                                     brush=(0, 0, 0, 0), size=10, pxMode=True)
        xVals = np.linspace(int(np.min(self._ionsVals['m/z']))-100, int(np.max(self._ionsVals['m/z']))+100, 1000)
        yVals = [-(self._solution[0]*x**2+(self._solution[1]-1)*x+self._solution[2]) for x in xVals]
        curve = pg.PlotCurveItem(x=xVals, y=yVals, pen=pg.mkPen(color='k', width=1))
        self._plot1.addItem(scatter)
        self._plot1.addItem(curve)
        self._layout.addWidget(self._plot1)


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
        pass