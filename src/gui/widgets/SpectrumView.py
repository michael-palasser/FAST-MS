import pyqtgraph as pg
from PyQt5 import QtWidgets, QtCore
import numpy as np

from src.gui.GUI_functions import setIcon

'''class BarGraphItem(pg.BarGraphItem):

    # constructor which inherit original
    # BarGraphItem
    def __init__(self, *args, **kwargs):
        pg.BarGraphItem.__init__(self, *args, **kwargs)

    # creating parent changed event
    def mousePressEvent(self, event):
        # rotating the barrgaph
        # print the message
        print("Mouse Press Event", self.getData())'''


class AbstractSpectrumView(QtWidgets.QWidget):
    '''
    QWidget which shows a part of the spectrum. Superclass of SpectrumView and TheoSpectrumView.
    '''
    def __init__(self, parent, peaks, ions, minRange, maxRange, maxY, lblSize):
        super(AbstractSpectrumView, self).__init__(parent)
        self._peaks = peaks
        self._ions = ions
        self._items = []
        self._layout = QtWidgets.QVBoxLayout(self)
        self._translate = QtCore.QCoreApplication.translate
        width = 0.02
        styles = {"black": "#f00", "font-size": lblSize}
        self._graphWidget = pg.PlotWidget(self)
        self._graphWidget.setLabel('left', 'signal', **styles)
        self._graphWidget.setLabel("bottom", "m/z", **styles)
        self._graphWidget.setBackground('w')
        self._graphWidget.setXRange(minRange, maxRange, padding=0)
        self._graphWidget.setYRange(0, maxY * 1.1, padding=0)
        baseLine = pg.InfiniteLine(pos=0,angle=0,pen='k',movable=False)
        self._graphWidget.addItem(baseLine)
        self.plot(width, True) #ToDo: Correct Width (linear fct)
        self.makeWidthWidgets(width)
        self._mzRange = range(int(min(self._peaks[:,0])), int(max(self._peaks[:,0]))+1)
        self._layout.addWidget(self._graphWidget)

        self._vb = self._graphWidget.plotItem.vb
        #print(np.average(self._peaks[:,0]))
        #self._cursorLabel = pg.TextItem(text='Hello' ,anchor=(0,0))
        self._cursorLabel = QtWidgets.QLabel(self)
        self._cursorLabel.setGeometry(QtCore.QRect(85, 40, 80, 52))
        #self._cursorLabel.setStyleSheet("border: 0.1px solid black;")
        #self._graphWidget.addItem(self._cursorLabel)
        pg.SignalProxy(self._graphWidget.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)
        self._graphWidget.scene().sigMouseMoved.connect(self.mouseMoved)
        pg.SignalProxy(self._graphWidget.scene().sigMouseMoved, rateLimit=60, slot=self.mouseClicked)
        self._graphWidget.scene().sigMouseClicked.connect(self.mouseClicked)
        setIcon(self)
        self._noise = None
        self.show()

    def mouseMoved(self, evt):
        pos = evt
        position = self._vb.mapSceneToView(pos)
        index = int(position.x())
        if index in self._mzRange:
            '''self._cursorLabel.setHtml(
                "<span style='font-size: 12pt'>x={:0.1f}, \
                 <span style='color: red'>y={:0.1f}</span>".format(
                    mousePoint.x(), mousePoint.y()))'''
            self._cursorLabel.setText(str(round(position.x(),5))+'\n' +str(round(position.y())))
            #self._cursorLabel.setAnchor((index, 0))

    def mouseClicked(self,evt):  # action if start button clicked
        # mousePoint = self._vb.mapSceneToView(pos)
        position = self._vb.mapSceneToView(evt.pos())
        index = int(position.x())
        #print(self._vb.mapSceneToView(position).x())
        #print(pos.x())
        if index in self._mzRange:
            print(position.x(), round(position.y()))
        '''else:
            print('not', mousePoint.x(), mousePoint.y())'''

    def makeWidthWidgets(self, width):
        self._spinBox = QtWidgets.QDoubleSpinBox(self)
        self._spinBox.setDecimals(3)
        self._spinBox.setValue(width)
        self._spinBox.setGeometry(QtCore.QRect(85, 10, 65, 26))
        self._spinBox.setToolTip("Change Width of Peaks (in Da)")
        try:
            self._spinBox.setStepType(QtWidgets.QAbstractSpinBox.AdaptiveDecimalStepType)
        except AttributeError as e:
            print(e)
        #self._cursorLabel = QtWidgets.QLabel(self)
        #self._cursorLabel.setGeometry(QtCore.QRect(70, 40, 200, 26))

    def plot(self, width, new=True):
        if new:
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
                self._items.append(scatter)
                maxMz = np.sort(ion.getIsotopePattern(), order='calcInt')[::-1]['m/z'][0]
                noise.append((maxMz, ion.getNoise()))
                self._graphWidget.addItem(scatter)
                self._legend.addItem(scatter, ion.getId())
                colourIndex += 1
            self._noise = np.array(noise)
            noiseLine = self._graphWidget.plot(self._noise[:, 0], self._noise[:, 1], pen='r')
            self._legend.addItem(noiseLine, 'noise')
        else:
            self._graphWidget.removeItem(self._peakBars)
            del self._peakBars
            self._peakBars = pg.BarGraphItem(x=self._peaks[:, 0], height=self._peaks[:, 1], width=width, brush='k')
            self._graphWidget.addItem(self._peakBars)

    def changeWidth(self):
        #self._graphWidget.removeItem(bars)
        self.plot(self._spinBox.value(), False)
        for item in self._items:
            self._graphWidget.removeItem(item)
            self._graphWidget.addItem(item)
        if self._noise is not None:
            self._graphWidget.plot(self._noise[:, 0], self._noise[:, 1], pen='r')
        self.show()


class SpectrumView(AbstractSpectrumView):
    '''
    QWidget which shows a part of the spectrum. Observed peaks are illustrated as black bars and isotope peaks with
     modelled intensities are shown as scatter plots.
    Used in top-down search.
    '''
    def __init__(self, parent, peaks, ions, minRange, maxRange, maxY):
        super(SpectrumView, self).__init__(parent, peaks, ions, minRange-1, maxRange+1, maxY, '18px')
        self._spinBox.valueChanged.connect(self.changeWidth)
        self.resize(700,400)


class TheoSpectrumView(AbstractSpectrumView):
    '''
    QWidget which shows a modelled peaks as red bars. Spectral intensities of this peaks are indicated by grey stars.
    Used in isotope pattern tool.
    '''
    def __init__(self, parent, peaks, width):
        spectrPeaks = np.array([(peak['m/z'],peak['relAb']) for peak in peaks])
        tolerance = (np.max(peaks['m/z'])-np.min(peaks['m/z']))*0.2
        yMax = max(np.max(peaks['calcInt']),np.max(peaks['relAb']))
        super(TheoSpectrumView, self).__init__(parent, spectrPeaks, peaks,
               np.min(peaks['m/z'])-tolerance, np.max(peaks['m/z'])+tolerance, yMax, "14px")
        self._spinBox.valueChanged.connect(self.changeWidth)
        self._spinBox.move(width - 70, 0)

    def plot(self, width, new):
        self._peakBars = pg.BarGraphItem(x=self._ions['m/z'], height=self._ions['calcInt'],
                                             pen =pg.mkPen(color='r', width=0.4), width=width, brush='r')
        self._graphWidget.addItem(self._peakBars)
        if len(self._peaks)>0:
            self._peakScatter = pg.ScatterPlotItem(x=self._peaks[:, 0], y=self._peaks[:, 1], symbol='star',
                                                   pen=pg.mkPen(color='k', width=0.2), size=12, pxMode=True)
            self._graphWidget.addItem(self._peakScatter)

