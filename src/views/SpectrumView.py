import sys

import pyqtgraph as pg
from PyQt5 import QtWidgets, QtCore
import numpy as np
from PyQt5.QtWidgets import QInputDialog

mz = [500.1,500.2,500.3,500.4]
Int1 = [1*10**6, 1.8*10**6, 1.7*10**6, 0.8*10**6 ]
peaks = np.array([[500.1,1*10**6],
         [500.2,1.8*10**6],
         [500.3, 1.7*10**6],
         [500.4, 0.8*10**6]])
modelled = \
    {'c05':np.array([[500.1, 0.5*10**6],
                    [500.3, 1*10**6]]),
         'w05':np.array([[500.1, 0.55 * 10 ** 6],
                  [500.2, .8 * 10 ** 6],
                  [500.3, .7 * 10 ** 6],
                  [500.4, 0.4 * 10 ** 6]])}


"""class SpectrumView(pg.PlotWidget()):
    def __init__(self, mz, Int):
        super(SpectrumView, self).__init__()
        styles = {"black": "#f00", "font-size": "20px"}
        self.setLabel('left', 'Rel.Ab.in AMU *10^6', **styles)
        self.setLabel("bottom", "m/z", **styles)

        self.addLegend()

        self.setXRange(min(mz)-2, max(mz)+2, padding=0)
        self.setYRange(0, max(Int1)+10^6, padding=0)
        peaks = pg.BarGraphItem(x=mz, height=Int, width=0.1, brush= 'r')
        self.addItem(peaks)"""
        #self.plot(mz, Int1)


"""class MyBarGraphItem(pg.BarGraphItem):

    def __init__(self):
        super().__init__()

    def setWidth(self, **opts):
        if 'width' in opts:
            self.width = opts['width']

        super().setOpts(**opts)"""

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, peaks, ions):
        super(MainWindow, self).__init__()
        """self.menubar = QtWidgets.QMenuBar(self.mainWindow)
        self.mainWindow.setMenuBar(self.menubar)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 340, 22))

        action = QtWidgets.QAction(self.mainWindow)
        action.setText(self._translate(self.mainWindow.objectName(), 'Change Peak Width'))
        action.triggered.connect(function)"""
        self.peaks = peaks
        self.ions = ions
        self.int = int
        self._translate = QtCore.QCoreApplication.translate
        self.width = 500
        self.hight = 400
        self.resize(self.width,self.hight)
        width = 0.01

        styles = {"black": "#f00", "font-size": "18px"}

        self.graphWidget = pg.PlotWidget()

        self.setCentralWidget(self.graphWidget)
        self.graphWidget.setLabel('left', 'Rel.Ab.in AMU', **styles)
        self.graphWidget.setLabel("bottom", "m/z", **styles)
        self.graphWidget.setBackground('w')
        self.graphWidget.setXRange(min(mz) - 1, max(mz) + 1, padding=0)
        self.graphWidget.setYRange(0, max(Int1) + 10 ** 5, padding=0)

        self.plot(width) #ToDo: Correct Width (linear fct)
        self.makeWidthWidgets(width)
        self.show()

    def makeWidthWidgets(self, width):
        self.spinBox = QtWidgets.QDoubleSpinBox(self.centralWidget())
        self.spinBox.setDecimals(3)
        self.spinBox.setValue(width)
        self.spinBox.move(65,10)
        self.spinBox.setToolTip("Change Width of Peaks (in Da)")
        self.pushButton = QtWidgets.QPushButton(self)
        self.pushButton.setGeometry(QtCore.QRect(60, 30, 70, 32))
        self.pushButton.setText(self._translate(self.objectName(), "Update"))
        self.pushButton.setToolTip("Change Width of Peaks (in Da)")
        self.pushButton.clicked.connect(self.changeWidth)

    def plot(self, width):
        self.peakBars = pg.BarGraphItem(x=self.peaks[:,0], height=self.peaks[:,1], width=width, brush='k')
        self.graphWidget.addItem(self.peakBars)
        colours = ['b','r','g', 'c', 'm','o', 'p', 'v']
        self.legend = pg.LegendItem(offset=(0., .5))
        self.legend.setParentItem(self.graphWidget.graphicsItem())
        #self.legend.addItem(self.aps_model, '')
        for i, ion in enumerate(self.ions.keys()):
            scatter = pg.ScatterPlotItem(x=self.ions[ion][:,0], y=self.ions[ion][:,1], symbol='o',
                                         pen =pg.mkPen(color=colours[i], width=2),
                                         brush=(50,50,200,50), size=8, pxMode=True) #Todo resize
            self.graphWidget.addItem(scatter)
            self.legend.addItem(scatter, ion)
            #self.graphWidget.plot(ion[:,0], ion[:,1], symbol='o', symbolSize=30, symbolBrush=('b'))


    def changeWidth(self):
        """width, ok = QInputDialog.getDouble(self, "Change Peak Width", "Enter Peak Width in Da: ")
        if ok:"""
        """if self.bars.x[i] - self.bars.width / 2 < pos.x() < self.bars.x[i] + self.bars.width / 2 \
                    and 0 < pos.y() < self.bars.height[i]:"""
            #w = self.peak
            #b[i] = pg.QtGui.QColor(255, 255, 255)
        self.graphWidget.removeItem(self.peakBars)
        self.plot(self.spinBox.value())
        #self.peakBars = pg.BarGraphItem(x=self.peaks[:,0], height=self.peaks[:,1], width=self.spinBox.value(), brush='k')
        #self.graphWidget.addItem(self.peakBars)
        self.show()
        #print('clicked on bar ' + str(i))


def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow(peaks, modelled)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()