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

class SpectrumView(QtWidgets.QMainWindow):

    def __init__(self, parent, peaks, ions, minRange, maxRange, maxY):
        super(SpectrumView, self).__init__(parent)
        self.peaks = peaks
        self.ions = ions
        self.int = int
        self._translate = QtCore.QCoreApplication.translate
        self.width = 700
        self.hight = 400
        self.resize(self.width,self.hight)
        width = 0.02

        styles = {"black": "#f00", "font-size": "18px"}

        self.graphWidget = pg.PlotWidget()

        self.setCentralWidget(self.graphWidget)
        #self.vb = pg.GraphicsLayout().addViewBox(self.graphWidget)
        #self.vb.setLimits(yMin=0)
        self.graphWidget.setLabel('left', 'Rel.Ab.in au', **styles)
        self.graphWidget.setLabel("bottom", "m/z", **styles)
        self.graphWidget.setBackground('w')
        self.graphWidget.setXRange(minRange - 1, maxRange+1, padding=0)
        self.graphWidget.setYRange(0, maxY*1.1, padding=0)
        baseLine = pg.InfiniteLine(pos=0,angle=0,pen='k',movable=False)
        self.graphWidget.addItem(baseLine)

        self.plot(width) #ToDo: Correct Width (linear fct)
        self.makeWidthWidgets(width)

        self.show()
        print('finished')

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
        colours = ['b','r','g', 'c', 'm', 'y']
        markers = ['o','t', 's', 'p','h', 'star', '+', 'd', 'x', 't1','t2', 't3']
        self.legend = pg.LegendItem(offset=(0., .5), labelTextSize='12pt')
        self.legend.setParentItem(self.graphWidget.graphicsItem())
        #self.legend.addItem(self.aps_model, '')
        noise = []
        markerIndex = 0
        colourIndex = 0
        for ion in self.ions:
            if colourIndex == len(colours):
                colourIndex = 0
                markerIndex += 1
                if markerIndex == len(markers):
                    markerIndex = 0
            scatter = pg.ScatterPlotItem(x=ion.isotopePattern['m/z'], y=ion.isotopePattern['calcInt'],
                                         symbol=markers[markerIndex],
                                         pen =pg.mkPen(color=colours[colourIndex], width=2),
                                         brush=(50,50,200,50), size=10, pxMode=True) #Todo resize"""
            maxMz = np.sort(ion.isotopePattern, order='calcInt')[::-1]['m/z'][0]
            print((maxMz, ion.noise))
            noise.append((maxMz, ion.noise))
            """scatter = pg.ScatterPlotItem(x=self.ions[ion][:,0], y=self.ions[ion][:,1], symbol=markers[markerIndex],
                                         pen =pg.mkPen(color=colours[colourIndex], width=2),
                                         brush=(50,50,200,50), size=10, pxMode=True) #Todo resize"""
            self.graphWidget.addItem(scatter)
            self.legend.addItem(scatter, ion.getName() + ', ' + str(ion.charge))
            colourIndex += 1
            #self.graphWidget.plot(ion[:,0], ion[:,1], symbol='o', symbolSize=30, symbolBrush=('b'))
        noise = np.array(noise)
        noiseLine = self.graphWidget.plot(noise[:,0],noise[:,1], pen='r')
        #self.graphWidget.addItem(noiseLine)
        self.legend.addItem(noiseLine, 'noise')

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
    main = SpectrumView(peaks, modelled)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()