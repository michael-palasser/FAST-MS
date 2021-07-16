import pyqtgraph as pg
from PyQt5 import QtWidgets, QtCore
import numpy as np


class AbstractSpectrumView(QtWidgets.QWidget):
    '''
    QWidget which shows a part of the spectrum. Superclass of SpectrumView and TheoSpectrumView.
    '''
    def __init__(self, parent, peaks, ions, minRange, maxRange, maxY, lblSize):
        super(AbstractSpectrumView, self).__init__(parent)
        self._peaks = peaks
        self._ions = ions
        self._translate = QtCore.QCoreApplication.translate
        width = 0.02
        self._layout=QtWidgets.QVBoxLayout(self)
        styles = {"black": "#f00", "font-size": lblSize}
        self._graphWidget = pg.PlotWidget(self)
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


    def makeWidthWidgets(self, width):
        self._spinBox = QtWidgets.QDoubleSpinBox(self)
        self._spinBox.setDecimals(3)
        self._spinBox.setValue(width)
        self._spinBox.setGeometry(QtCore.QRect(70, 10, 65, 26))
        self._spinBox.setToolTip("Change Width of Peaks (in Da)")
        self._spinBox.setStepType(QtWidgets.QAbstractSpinBox.AdaptiveDecimalStepType)

    def plot(self, width):
        self._peakBars = pg.BarGraphItem(x=self._peaks[:, 0], height=self._peaks[:, 1], width=width, brush='k')
        self._graphWidget.addItem(self._peakBars)
        colours = ['b','r','g', 'c', 'm', 'y']
        markers = ['o','t', 's', 'p','h', 'star', '+', 'd', 'x', 't1','t2', 't3']
        self._legend = pg.LegendItem(offset=(0., .5), labelTextSize='12pt')
        self._legend.setParentItem(self._graphWidget.graphicsItem())
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
            self._graphWidget.addItem(scatter)
            self._legend.addItem(scatter, ion.getId())
            colourIndex += 1
        noise = np.array(noise)
        noiseLine = self._graphWidget.plot(noise[:, 0], noise[:, 1], pen='r')
        self._legend.addItem(noiseLine, 'noise')

    def changeWidth(self, bars):
        self._graphWidget.removeItem(bars)
        self.plot(self._spinBox.value())
        self.show()


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
        self._spinBox.move(width - 70, 0)

    def plot(self, width):
        self._modelledBars = pg.BarGraphItem(x=self._ions['m/z'], height=self._ions['calcInt'],
                                             pen =pg.mkPen(color='r', width=0.4), width=width, brush='r')
        self._graphWidget.addItem(self._modelledBars)
        if len(self._peaks)>0:
            self._peakScatter = pg.ScatterPlotItem(x=self._peaks[:, 0], y=self._peaks[:, 1], symbol='star',
                                                   pen=pg.mkPen(color='k', width=0.2), size=12, pxMode=True)
            self._graphWidget.addItem(self._peakScatter)

