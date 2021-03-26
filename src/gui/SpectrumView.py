import sys

import pyqtgraph as pg
from PyQt5 import QtWidgets, QtCore
import numpy as np
#from PyQt5.QtWidgets import QInputDialog

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

class AbstractSpectrumView(QtWidgets.QWidget):
    def __init__(self, parent, peaks, ions, minRange, maxRange, maxY, lblSize):
        super(AbstractSpectrumView, self).__init__(parent)
        self.peaks = peaks
        self.ions = ions
        self.int = int
        self._translate = QtCore.QCoreApplication.translate
        #self.width = 700
        #self.hight = 400
        #self.resize(self.width,self.hight)
        width = 0.02
        self.layout=QtWidgets.QVBoxLayout(self)
        styles = {"black": "#f00", "font-size": lblSize}
        self.graphWidget = pg.PlotWidget(self)
        #self.setCentralWidget(self.graphWidget)
        #self.vb = pg.GraphicsLayout().addViewBox(self.graphWidget)
        #self.vb.setLimits(yMin=0)
        self.graphWidget.setLabel('left', 'Rel.Ab.in au', **styles)
        self.graphWidget.setLabel("bottom", "m/z", **styles)
        self.graphWidget.setBackground('w')
        self.graphWidget.setXRange(minRange, maxRange, padding=0)
        self.graphWidget.setYRange(0, maxY*1.1, padding=0)
        baseLine = pg.InfiniteLine(pos=0,angle=0,pen='k',movable=False)
        self.graphWidget.addItem(baseLine)

        self.plot(width) #ToDo: Correct Width (linear fct)
        self.makeWidthWidgets(width)

        self.layout.addWidget(self.graphWidget)
        self.show()

    #def setLabels(self):

    def makeWidthWidgets(self, width):
        '''self.widthWidget = QtWidgets.QWidget(self)
        self.widthWidget.setGeometry(QtCore.QRect(65, 10, 70, 58))'''
        self.spinBox = QtWidgets.QDoubleSpinBox(self)
        self.spinBox.setDecimals(3)
        self.spinBox.setValue(width)
        #self.spinBox.move(65,10)
        self.spinBox.setGeometry(QtCore.QRect(70, 10, 65, 26))
        #self.spinBox.setGeometry(QtCore.QRect(65, 10, 65, 26))
        self.spinBox.setToolTip("Change Width of Peaks (in Da)")
        self.spinBox.setStepType(QtWidgets.QAbstractSpinBox.AdaptiveDecimalStepType)
        '''self.pushButton = QtWidgets.QPushButton(self.widthWidget)
        self.pushButton.setGeometry(QtCore.QRect(0, 22, 70, 32))
        #self.pushButton.setGeometry(QtCore.QRect(60, 32, 70, 32))
        self.pushButton.setText(self._translate(self.objectName(), "Update"))
        self.pushButton.setToolTip("Change Width of Peaks (in Da)")
        self.pushButton.clicked.connect(lambda: self.changeWidth(self.peakBars))'''

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
            scatter = pg.ScatterPlotItem(x=ion.getIsotopePattern()['m/z'], y=ion.getIsotopePattern()['calcInt'],
                                         symbol=markers[markerIndex],
                                         pen =pg.mkPen(color=colours[colourIndex], width=2),
                                         brush=(50,50,200,50), size=10, pxMode=True) #Todo resize"""
            maxMz = np.sort(ion.getIsotopePattern(), order='calcInt')[::-1]['m/z'][0]
            noise.append((maxMz, ion.getNoise()))
            """scatter = pg.ScatterPlotItem(x=self.ions[ion][:,0], y=self.ions[ion][:,1], symbol=markers[markerIndex],
                                         pen =pg.mkPen(color=colours[colourIndex], width=2),
                                         brush=(50,50,200,50), size=10, pxMode=True) #Todo resize"""
            self.graphWidget.addItem(scatter)
            self.legend.addItem(scatter, ion.getId())
            colourIndex += 1
            #self.graphWidget.plot(ion[:,0], ion[:,1], symbol='o', symbolSize=30, symbolBrush=('b'))
        noise = np.array(noise)
        noiseLine = self.graphWidget.plot(noise[:,0],noise[:,1], pen='r')
        #self.graphWidget.addItem(noiseLine)
        self.legend.addItem(noiseLine, 'noise')

    def changeWidth(self, bars):
        """width, ok = QInputDialog.getDouble(self, "Change Peak Width", "Enter Peak Width in Da: ")
        if ok:"""
        """if self.bars.x[i] - self.bars.width / 2 < pos.x() < self.bars.x[i] + self.bars.width / 2 \
                    and 0 < pos.y() < self.bars.height[i]:"""
            #w = self.peak
            #b[i] = pg.QtGui.QColor(255, 255, 255)
        self.graphWidget.removeItem(bars)
        self.plot(self.spinBox.value())
        #self.peakBars = pg.BarGraphItem(x=self.peaks[:,0], height=self.peaks[:,1], width=self.spinBox.value(), brush='k')
        #self.graphWidget.addItem(self.peakBars)
        self.show()
        #print('clicked on bar ' + str(i))

class SpectrumView(AbstractSpectrumView):
    def __init__(self, parent, peaks, ions, minRange, maxRange, maxY):
        super(SpectrumView, self).__init__(parent, peaks, ions, minRange-1, maxRange+1, maxY, '18px')
        self.spinBox.valueChanged.connect(lambda: self.changeWidth(self.peakBars))
        self.resize(700,400)

class TheoSpectrumView(AbstractSpectrumView):
    def __init__(self, parent, peaks, width):
        spectrPeaks = np.array([(peak['m/z'],peak['relAb']) for peak in peaks])
        tolerance = (np.max(peaks['m/z'])-np.min(peaks['m/z']))*0.2
        super(TheoSpectrumView, self).__init__(parent, spectrPeaks, peaks,
               np.min(peaks['m/z'])-tolerance, np.max(peaks['m/z'])+tolerance, np.max(peaks['calcInt']), "14px")
        self.spinBox.valueChanged.connect(lambda: self.changeWidth(self.modelledBars))
        #styles = {"black": "#f00", "font-size": "14px"}
        #self.setCentralWidget(self.graphWidget)
        #self.vb = pg.GraphicsLayout().addViewBox(self.graphWidget)
        #self.vb.setLimits(yMin=0)
        #self.graphWidget.setLabel('left', 'Rel.Ab.in au', **styles)
        #self.graphWidget.setLabel("bottom", "m/z", **styles)
        #self.setGeometry(QtCore.QRect(270, 30, 300, 290))
        self.spinBox.move(width-70,0)
        #self.resize(500, 400)
        #self.spinBox.setValue(0.4)
        #self.pushButton.clicked.disconnect()
        #self.pushButton.clicked.connect(lambda: self.changeWidth(self.modelledBars))

    def plot(self, width):
        #self.legend = pg.LegendItem(offset=(0., .5), labelTextSize='12pt')
        #self.legend.setParentItem(self.graphWidget.graphicsItem())
        self.modelledBars = pg.BarGraphItem(x=self.ions['m/z'], height=self.ions['calcInt'],
                                            pen =pg.mkPen(color='r', width=0.4), width=width, brush='r')
        self.graphWidget.addItem(self.modelledBars)
        if len(self.peaks)>0:
            self.peakScatter = pg.ScatterPlotItem(x=self.peaks[:,0], y=self.peaks[:,1], symbol='star',
                                                  pen=pg.mkPen(color='k', width=0.2), size=12, pxMode=True)
            self.graphWidget.addItem(self.peakScatter)
        #self.legend.addItem(self.modelledBars, 'modelled')

    '''def changeWidth(self):
        self.graphWidget.removeItem(self.modelledBars)
        self.plot(self.spinBox.value())
        self.show()'''

def main():
    app = QtWidgets.QApplication(sys.argv)
    main = SpectrumView(None,peaks, modelled,500,501,12*10**6)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()