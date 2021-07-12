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
    '''
    QWidget which shows a part of the spectrum. Superclass of SpectrumView and TheoSpectrumView.
    '''
    def __init__(self, parent, peaks, ions, minRange, maxRange, maxY, lblSize):
        super(AbstractSpectrumView, self).__init__(parent)
        self._peaks = peaks
        self._ions = ions
        self._translate = QtCore.QCoreApplication.translate
        #self.width = 700
        #self.hight = 400
        #self.resize(self.width,self.hight)
        width = 0.02
        self._layout=QtWidgets.QVBoxLayout(self)
        styles = {"black": "#f00", "font-size": lblSize}
        self._graphWidget = pg.PlotWidget(self)
        #self.setCentralWidget(self._graphWidget)
        #self.vb = pg.GraphicsLayout().addViewBox(self._graphWidget)
        #self.vb.setLimits(yMin=0)
        self._graphWidget.setLabel('left', 'Rel.Ab.in au', **styles)
        self._graphWidget.setLabel("bottom", "m/z", **styles)
        self._graphWidget.setBackground('w')
        self._graphWidget.setXRange(minRange, maxRange, padding=0)
        self._graphWidget.setYRange(0, maxY * 1.1, padding=0)
        baseLine = pg.InfiniteLine(pos=0,angle=0,pen='k',movable=False)
        self._graphWidget.addItem(baseLine)

        self.plot(width) #ToDo: Correct Width (linear fct)
        self.makeWidthWidgets(width)

        self._layout.addWidget(self._graphWidget)
        self.show()

    #def setLabels(self):

    def makeWidthWidgets(self, width):
        '''self.widthWidget = QtWidgets.QWidget(self)
        self.widthWidget.setGeometry(QtCore.QRect(65, 10, 70, 58))'''
        self._spinBox = QtWidgets.QDoubleSpinBox(self)
        self._spinBox.setDecimals(3)
        self._spinBox.setValue(width)
        #self._spinBox.move(65,10)
        self._spinBox.setGeometry(QtCore.QRect(70, 10, 65, 26))
        #self._spinBox.setGeometry(QtCore.QRect(65, 10, 65, 26))
        self._spinBox.setToolTip("Change Width of Peaks (in Da)")
        self._spinBox.setStepType(QtWidgets.QAbstractSpinBox.AdaptiveDecimalStepType)
        '''self._pushButton = QtWidgets.QPushButton(self.widthWidget)
        self._pushButton.setGeometry(QtCore.QRect(0, 22, 70, 32))
        #self._pushButton.setGeometry(QtCore.QRect(60, 32, 70, 32))
        self._pushButton.setText(self._translate(self.objectName(), "Update"))
        self._pushButton.setToolTip("Change Width of Peaks (in Da)")
        self._pushButton.clicked.connect(lambda: self.changeWidth(self._peakBars))'''

    def plot(self, width):
        self._peakBars = pg.BarGraphItem(x=self._peaks[:, 0], height=self._peaks[:, 1], width=width, brush='k')
        self._graphWidget.addItem(self._peakBars)
        colours = ['b','r','g', 'c', 'm', 'y']
        markers = ['o','t', 's', 'p','h', 'star', '+', 'd', 'x', 't1','t2', 't3']
        self._legend = pg.LegendItem(offset=(0., .5), labelTextSize='12pt')
        self._legend.setParentItem(self._graphWidget.graphicsItem())
        #self._legend.addItem(self.aps_model, '')
        noise = []
        markerIndex = 0
        colourIndex = 0
        for ion in self._ions:
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
            self._graphWidget.addItem(scatter)
            self._legend.addItem(scatter, ion.getId())
            colourIndex += 1
            #self._graphWidget.plot(ion[:,0], ion[:,1], symbol='o', symbolSize=30, symbolBrush=('b'))
        noise = np.array(noise)
        noiseLine = self._graphWidget.plot(noise[:, 0], noise[:, 1], pen='r')
        #self._graphWidget.addItem(noiseLine)
        self._legend.addItem(noiseLine, 'noise')

    def changeWidth(self, bars):
        """width, ok = QInputDialog.getDouble(self, "Change Peak Width", "Enter Peak Width in Da: ")
        if ok:"""
        """if self.bars.x[i] - self.bars.width / 2 < pos.x() < self.bars.x[i] + self.bars.width / 2 \
                    and 0 < pos.y() < self.bars.height[i]:"""
            #w = self.peak
            #b[i] = pg.QtGui.QColor(255, 255, 255)
        self._graphWidget.removeItem(bars)
        self.plot(self._spinBox.value())
        #self._peakBars = pg.BarGraphItem(x=self.peaks[:,0], height=self.peaks[:,1], width=self._spinBox.value(), brush='k')
        #self._graphWidget.addItem(self._peakBars)
        self.show()
        #print('clicked on bar ' + str(i))

class SpectrumView(AbstractSpectrumView):
    '''
    QWidget which shows a part of the spectrum. Observed peaks are illustrated as black bars and isotope peaks with
     modelled intensities are shown as scatter plots.
    Used in top-down search.
    '''
    def __init__(self, parent, peaks, ions, minRange, maxRange, maxY):
        super(SpectrumView, self).__init__(parent, peaks, ions, minRange-1, maxRange+1, maxY, '18px')
        self._spinBox.valueChanged.connect(lambda: self.changeWidth(self._peakBars))
        self.resize(700,400)

class TheoSpectrumView(AbstractSpectrumView):
    '''
    QWidget which shows a modelled peaks as red bars. Spectral intensities of this peaks are indicated by grey stars.
    Used in isotope pattern tool.
    '''
    def __init__(self, parent, peaks, width):
        spectrPeaks = np.array([(peak['m/z'],peak['relAb']) for peak in peaks])
        tolerance = (np.max(peaks['m/z'])-np.min(peaks['m/z']))*0.2
        super(TheoSpectrumView, self).__init__(parent, spectrPeaks, peaks,
               np.min(peaks['m/z'])-tolerance, np.max(peaks['m/z'])+tolerance, np.max(peaks['calcInt']), "14px")
        self._spinBox.valueChanged.connect(lambda: self.changeWidth(self._modelledBars))
        #styles = {"black": "#f00", "font-size": "14px"}
        #self.setCentralWidget(self._graphWidget)
        #self.vb = pg.GraphicsLayout().addViewBox(self._graphWidget)
        #self.vb.setLimits(yMin=0)
        #self._graphWidget.setLabel('left', 'Rel.Ab.in au', **styles)
        #self._graphWidget.setLabel("bottom", "m/z", **styles)
        #self.setGeometry(QtCore.QRect(270, 30, 300, 290))
        self._spinBox.move(width - 70, 0)
        #self.resize(500, 400)
        #self._spinBox.setValue(0.4)
        #self._pushButton.clicked.disconnect()
        #self._pushButton.clicked.connect(lambda: self.changeWidth(self._modelledBars))

    def plot(self, width):
        #self._legend = pg.LegendItem(offset=(0., .5), labelTextSize='12pt')
        #self._legend.setParentItem(self._graphWidget.graphicsItem())
        self._modelledBars = pg.BarGraphItem(x=self._ions['m/z'], height=self._ions['calcInt'],
                                             pen =pg.mkPen(color='r', width=0.4), width=width, brush='r')
        self._graphWidget.addItem(self._modelledBars)
        if len(self._peaks)>0:
            self._peakScatter = pg.ScatterPlotItem(x=self._peaks[:, 0], y=self._peaks[:, 1], symbol='star',
                                                   pen=pg.mkPen(color='k', width=0.2), size=12, pxMode=True)
            self._graphWidget.addItem(self._peakScatter)
        #self._legend.addItem(self._modelledBars, 'modelled')

    '''def changeWidth(self):
        self._graphWidget.removeItem(self._modelledBars)
        self.plot(self._spinBox.value())
        self.show()'''

def main():
    app = QtWidgets.QApplication(sys.argv)
    main = SpectrumView(None,peaks, modelled,500,501,12*10**6)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()