import pyqtgraph as pg
from PySide6 import QtWidgets
from PySide6.QtCore import QRect
from PySide6.QtGui import QFont
import numpy as np

#Delete if not working
import platform
import ctypes
if platform.system()=='Windows' and int(platform.release()) >= 8:   
    ctypes.windll.shcore.SetProcessDpiAwareness(True)

from src.gui.GUI_functions import setWindowIcon, translate

pg.setConfigOptions(antialias=True)

class AbstractSpectrumView(QtWidgets.QWidget):
    '''
    QWidget which shows a part of the spectrum. Superclass of SpectrumView and TheoSpectrumView.
    '''
    def __init__(self, parent, title, peaks, ions, minRange, maxRange, maxY, ionMode, noise=None, focused=False,
                 profileSpec=None):
        super(AbstractSpectrumView, self).__init__(parent)
        self._peaks = peaks
        self._profileSpec=profileSpec
        self._ions = ions
        self._items = []
        if ionMode>0:
            self._ionMode = "+"
        else:
            self._ionMode = "-"
        self._noise = noise
        if self._noise is None:
            self._noise = self.getNoiseArray()
        self._focused = focused
        self._layout = QtWidgets.QVBoxLayout(self)
        self._translate = translate
        styles = {"color": "black"}
        self._graphWidget = pg.PlotWidget(self, axisItems={'left': SciAxis(orientation='left')})
        self._graphWidget.setLabel('left', 'signal', **styles)
        self._graphWidget.setLabel("bottom", "m/z", **styles)
        for axisName in ("left", "bottom"):
            self._font=QFont()
            self._font.setPointSize(10)
            axis = self._graphWidget.getAxis(axisName)
            axis.setStyle(tickFont=self._font)
            axis.label.setFont(self._font)
            axis.setTextPen('k')
            axis.setPen(pg.mkPen(color="k", width=0.5))
            if axisName=="left":
                axis.setTickSpacing(minor=None)
        self._graphWidget.setBackground('w')
        self._vb = self._graphWidget.plotItem.vb
        baseLine = pg.InfiniteLine(pos=0,angle=0,pen='k',movable=False)
        self._graphWidget.addItem(baseLine)
        self._width = 0.02
        self.plot(focused, True) #ToDo: Correct Width (linear fct)
        self._padding = 1.1
        self.setWindow(minRange-self._padding, maxRange+self._padding,maxY)
        pg.SignalProxy(self._graphWidget.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)
        self._graphWidget.scene().sigMouseMoved.connect(self.mouseMoved)
        self._clicks = []
        pg.SignalProxy(self._graphWidget.scene().sigMouseMoved, rateLimit=60, slot=self.mouseClicked)
        self._graphWidget.scene().sigMouseClicked.connect(self.mouseClicked)
        self._layout.addWidget(self._graphWidget)
        self._cursorLabel = QtWidgets.QLabel(self)
        self._cursorLabel.setGeometry(QRect(85, 40, 80, 52))
        setWindowIcon(self)
        if focused:
            title = self._focused[0] + ", " +str(self._focused[1])+self._ionMode +" (" + title+")"
        self.setWindowTitle(title)
        self.show()

    def getGraphWidget(self,legend=True):
        if not legend:
            self._graphWidget.scene().removeItem( self._legend)
            self._graphWidget.removeItem(self._peakBars)
        return self._graphWidget

    def makePic(self):
        self._graphWidget.scene().removeItem( self._legend)

    def getNoiseArray(self):
        noise = []
        for ion in self._ions:
            maxMz = np.sort(ion.getIsotopePattern(), order='calcInt')[::-1]['m/z'][0]
            noise.append((maxMz, ion.getNoise()))
        return np.sort(np.array(noise, dtype=[('m/z', float), ('I', float)]), order='m/z')


    def setWindow(self, minRange, maxRange,maxY):
        self._mzRange = range(int(min(self._peaks['m/z'])), int(max(self._peaks['m/z']))+1)
        maxInt = np.max(self._peaks["I"])     #total maximum
        vbMin, vbMax = np.min(self._peaks["m/z"]), np.max(self._peaks["m/z"])
        if vbMin>minRange:
            vbMin = minRange
        if vbMax<maxRange:
            vbMax = maxRange
        self._vb.setLimits(xMin=vbMin, xMax=vbMax, yMin=-0.005*maxInt, yMax=maxInt*1.4)
        self._graphWidget.setXRange(minRange-self._padding, maxRange+self._padding, padding=0)
        self._graphWidget.setYRange(0, maxY * 1.1, padding=0)

    def mouseMoved(self, evt):
        pos = evt
        position = self._vb.mapSceneToView(pos)
        index = int(position.x())
        if index in self._mzRange:
            self._cursorLabel.setText(str(round(position.x(),5))+'\n' +str(round(position.y())))

    def mouseClicked(self,evt):  # action if start button clicked
        scene_coords = evt.scenePos()
        if self._graphWidget.sceneBoundingRect().contains(scene_coords):
            point =self._vb.mapSceneToView(scene_coords)
            x = round(point.x(),5)
            y = round(point.y())
            print("\t",x, y)
            if len(self._clicks)==0:  # First mouse click - ONLY register coordinates
                self._clicks.append((x,y))
            elif len(self._clicks)==1:  # Second mouse click - register coordinates of second click
                self._clicks.append((x,y))
                distance = self._clicks[1][0]-self._clicks[0][0]
                if distance !=0:
                    print("distance:",round(distance,3), "; charge:",abs(round(1/distance,1)))
                # reset clicks array
                self._clicks = [] # this resets the *content* of clicks without changing the object itself
            else:  # something went wrong, just reset clicks
                self._clicks = []

    def plot(self, focused:bool, new=True):
        if new:
            if self._profileSpec is not None:
                self._width = 0.002
                self._profile = pg.PlotCurveItem(x=self._profileSpec['m/z'], y=self._profileSpec['I'],
                                           pen=pg.mkPen(color='k', width=0.5))
                # send to back
                self._graphWidget.addItem(self._profile)
                self._items.append(self._profile)
            self._peakBars = pg.BarGraphItem(x=self._peaks['m/z'], height=self._peaks['I'], width=self._width, brush='k')
            self._graphWidget.addItem(self._peakBars)
            #colours = ['b','r','g', 'c', 'm', 'y']
            colours = ['b','r']+list({'ocean green':'#4FB06D', 'tab:cyan':'#17becf', 'fuchsia':'#D9027D',
                                      'Visitation':'#ffd700', 'Corn Green':'#71A92C',"brown": "#eab76a", 'Violet':'#9B26B6'}.values())
            markers = ['o','t', 's', 'p','h', 'star', '+', 'd', 'x', 't1','t2']#, 't3']
            maxIndizes = (len(colours), len(markers))
            coulour_index=0
            marker_index=0
            self._legend = pg.LegendItem(offset=(0., .5), labelTextSize='10pt', labelTextColor="k")
            self._legend.setParentItem(self._graphWidget.graphicsItem())
            if self._profileSpec is not None:
                self._legend.addItem(self._profile, "")#ion.getId())
                self._legend.addItem(self._peakBars, "peaks")#ion.getId())
                self._peakBars.hide()
            for ion in self._ions:
                if focused and ion.getHash()==self._focused:
                    symbol='o'
                    colour = (255, 165, 0)
                    size=12
                    brush = (255,255,0,50)
                else:
                    symbol=markers[marker_index]
                    colour = colours[coulour_index]
                    coulour_index += 1
                    marker_index+=1
                    size=10
                    brush = (255,255,0,50)
                scatter = pg.ScatterPlotItem(x=ion.getIsotopePattern()['m/z'], y=ion.getIsotopePattern()['calcInt'],
                                             symbol=symbol,
                                             pen =pg.mkPen(color=colour, width=2),
                                             brush=brush, size=size, pxMode=True) #Todo resize"""
                if ion.getCharge() ==1:
                    charge=""
                else:
                    charge = str(ion.getCharge())
                text = ion.getName(True)+"<sup>"+charge+self._ionMode+"</sup>"
                scatter.setToolTip(text)
                self._items.append(scatter)
                self._graphWidget.addItem(scatter)
                self._legend.addItem(scatter, text)
                if coulour_index == maxIndizes[0]:
                    coulour_index = 0
                if marker_index == maxIndizes[1]:
                    marker_index = 0
            if len(self._noise)>0:
                #self._noise = np.array(noise)
                if len(self._noise['m/z'])==1 or np.all(np.isclose(self._noise['m/z'], self._noise['m/z'][0], atol=10**-3)):
                    mz = self._noise['m/z'][0]
                    noise=self._noise['I'][0]
                    self._noiseLine = self._graphWidget.plot([mz-1,mz,mz+1], [noise, noise,noise], pen='r')
                else:
                    self._noiseLine = self._graphWidget.plot(self._noise['m/z'], self._noise['I'], pen='r')
                self._legend.addItem(self._noiseLine, 'noise')
                self._items.append(self._noiseLine)
        else:
            self._graphWidget.removeItem(self._peakBars)
            del self._peakBars
            self._peakBars = pg.BarGraphItem(x=self._peaks['m/z'], height=self._peaks['I'], width=self._width, brush='k')
            self._graphWidget.addItem(self._peakBars)



class SpectrumView(AbstractSpectrumView):
    '''
    QWidget which shows a part of the spectrum. Observed peaks are illustrated as black bars and isotope peaks with
     modelled intensities are shown as scatter plots.
    Used in top-down search.
    '''
    def __init__(self, parent, title, peaks, ions, minRange, maxRange, maxY, ionMode, noise=None, focused=False, profileSpec=None):
        super(SpectrumView, self).__init__(parent, title, peaks, ions, minRange-1, maxRange+1, maxY, ionMode, noise,
                                           focused, profileSpec)
        self.resize(700,400)

    def updateView(self, peaks, ions, minRange, maxRange, maxY, noise, focused=False, profileSpec=None):
        self._peaks = peaks
        self._profileSpec = profileSpec
        self._ions = ions
        self._noise = noise
        if self._noise is None:
            self._noise = self.getNoiseArray()
        self._focused = focused
        self._legend.scene().removeItem(self._legend)
        for item in self._items:
            self._graphWidget.removeItem(item)
            self._legend.removeItem(item)
            del item
        self._graphWidget.removeItem(self._peakBars)
        del self._peakBars
        self.plot(focused, True) #ToDo: Correct Width (linear fct)
        self._mzRange = range(int(min(self._peaks['m/z'])), int(max(self._peaks['m/z']))+1)
        self.setWindow(minRange-self._padding, maxRange+self._padding, maxY)

class TheoSpectrumView(AbstractSpectrumView):
    '''
    QWidget which shows a modelled peaks as red bars. Spectral intensities of this peaks are indicated by grey stars.
    Used in isotope pattern tool.
    '''
    def __init__(self, parent, peaks, width, ionMode):
        spectrPeaks = peaks[['m/z', 'I']]
        tolerance = (np.max(peaks['m/z'])-np.min(peaks['m/z']))*0.2
        yMax = max(np.max(peaks['calcInt']),np.max(peaks['I']))
        super(TheoSpectrumView, self).__init__(parent, "", spectrPeaks, peaks,
               np.min(peaks['m/z'])-tolerance, np.max(peaks['m/z'])+tolerance, yMax, ionMode,
                                               noise=[(0,0)])
        self.makeWidthWidgets()
        self._spinBox.move(width - 70, 0)

    def plot(self, width, new):
        self._peakBars = pg.BarGraphItem(x=self._ions['m/z'], height=self._ions['calcInt'],
                                             pen =pg.mkPen(color='r', width=0.4), width=width, brush='r')
        self._graphWidget.addItem(self._peakBars)
        if len(self._peaks)>0:
            self._peakScatter = pg.ScatterPlotItem(x=self._peaks['m/z'], y=self._peaks['I'], symbol='star',
                                                   pen=pg.mkPen(color='k', width=0.2), size=12, pxMode=True)
            self._graphWidget.addItem(self._peakScatter)


    def setWindow(self, minRange, maxRange,maxY):
        self._mzRange = range(int(min(self._peaks['m/z'])), int(max(self._peaks['m/z']))+1)
        maxInt = np.max(self._peaks["I"])     #total maximum
        if maxInt<maxY:
            maxInt=maxY
        self._vb.setLimits(xMin=minRange-0.5, xMax=maxRange+0.5, yMin=-0.005*maxInt, yMax=maxInt*1.4)
        self._graphWidget.setXRange(minRange-self._padding, maxRange+self._padding, padding=0)
        self._graphWidget.setYRange(0, maxY * 1.1, padding=0)


    def makeWidthWidgets(self):
        self._spinBox = QtWidgets.QDoubleSpinBox(self)
        self._spinBox.setDecimals(3)
        self._spinBox.setValue(self._width)
        self._spinBox.setGeometry(QRect(85, 10, 65, 26))
        self._spinBox.setToolTip("Change Width of Peaks (in Da)")
        self._spinBox.valueChanged.connect(self.changeWidth)
        try:
            self._spinBox.setStepType(QtWidgets.QAbstractSpinBox.StepType.AdaptiveDecimalStepType)
        except AttributeError as e:
            print(e)

    def changeWidth(self):
        self._width = self._spinBox.value()
        self.plot(self._width, False)
        for item in self._items:
            self._graphWidget.removeItem(item)
            self._graphWidget.addItem(item)
        self.show()


class SciAxis(pg.AxisItem):
    def tickStrings(self, values, scale, spacing):
        return [f"{v:.1e}" if v != 0 else "0" for v in values]


if __name__ == '__main__':
    pass
    #plot =  ProfileSpectrumView(parent, peaks, ions, minRange, maxRange, maxY, ionMode, profileSpec, noise=None, focused=False):


