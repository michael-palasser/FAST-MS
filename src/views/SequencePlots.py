import sys
from pyqtgraph.ptime import time
import numpy as np

from PyQt5 import QtCore, QtWidgets, QtGui
import pyqtgraph as pg


class PlotFactory(object):
    def __init__(self, parent):
        self._parent = parent
        '''self._colours = ['r', 'b', 'y', 'm', 'c', 'g']
        self._markers = ['o','t', 's', 'p','h', 'star', '+', 'd', 'x', 't1','t2', 't3']'''

    def showOccupancyPlot(self, sequence, forwardVals, backwardVals, maxY):
        self.initiatePlot(sequence, forwardVals, backwardVals, maxY, self.formatForOccupancies)

    def showChargePlot(self, sequence, forwardVals, backwardVals, maxY):
        self.initiatePlot(sequence, forwardVals, backwardVals, maxY, self.formatForCharges)

    def initiatePlot(self, sequence, forwardVals, backwardVals, maxY, func):
        #self.plotWdw = QtWidgets.QMainWindow(self._parent)
        self._forwardVals = forwardVals
        self._backwardVals = backwardVals
        self._sequence = sequence
        self._translate = QtCore.QCoreApplication.translate
        #self.plotWdw.resize(len(sequence) * 30 + 200, 400)
        self.p = pg.plot()
        self.p.addLegend(labelTextSize='12pt')
        self.p.setBackground('w')
        self.p.showAxis('right')
        self.p2 = pg.ViewBox()
        self.p.scene().addItem(self.p2)
        self.p.getAxis('right').linkToView(self.p2)
        self.p2.setXLink(self.p)
        self.p2.setYLink(self.p)
        styles = {"black": "#f00", "font-size": "18px"}
        self.p.setLabel('bottom', 'cleavage site', **styles)
        yRange = [-0.05,maxY+0.05]
        self.p.setXRange(0.01, len(self._sequence)+0.01)
        self.p.plotItem.vb.setLimits(xMin=0,xMax=len(self._sequence)+0.01, yMin=yRange[0], yMax=yRange[1])
        self.p.setRange(yRange=yRange, padding=0)
        self.p2.setRange(yRange=yRange, padding=0)
        self.p2.invertY()
        self.addSequence()
        #self.legend = pg.LegendItem(offset=(0., .5), labelTextSize='12pt')
        #self.legend.setParentItem(self.p)
        func()
        self.plot()
        #self.p = self.makeAxis(yLabel,forwardVals)

    def addSequence(self):
        line = pg.InfiniteLine(pos=0,angle=0,pen=pg.mkPen(color='w', width=0),movable=False)
        self.p.addItem(line)
        sequMarkers = {}
        for bb in self._sequence:
            if bb not in sequMarkers.keys():
                sequMarkers[bb] = self.makeCustomMarker(bb)
        for i, bb in enumerate(self._sequence):
            scatter = pg.ScatterPlotItem(x=(i+0.5,),y=(0.01,), symbol=sequMarkers[bb],
                                         pen=pg.mkPen(color='k', width=0.1), size=10, pxMode=True)
            self.p.addItem(scatter)

    def formatForCharges(self):
        self.p.setWindowTitle( 'Charge Distribution')
        yLabel = 'average charge '
        styles = {"black": "#f00", "font-size": "18px"}
        self.p.setLabel('left', yLabel+','.join(self._forwardVals.keys()), **styles)
        self.p.setLabel('right', yLabel+','.join(self._backwardVals.keys()), **styles)

    def formatForOccupancies(self):
        self.p.setWindowTitle( 'Occupancies')
        yLabel = 'occupancy '
        styles = {"black": "#f00", "font-size": "18px"}
        self.p.setLabel('left', yLabel+','.join(self._forwardVals.keys()), units='%', **styles)
        self.p.setLabel('right', yLabel+','.join(self._backwardVals.keys()), units='%', **styles)

    def plot(self):
        colours = ['r', 'b', 'y', 'm', 'c', 'g']
        markers = ['o', 't', 's', 'p', 'h', 'star', '+', 'd', 'x', 't1', 't2', 't3']
        xVals = [i+1 for i in range(len(self._sequence))]
        self.plotCurve(xVals, self._forwardVals, colours, markers,self.p)
        self.plotCurve(xVals, self._backwardVals, colours[::-1], markers[::-1],self.p2)
        self.updateViews()
        self.p.getViewBox().sigResized.connect(self.updateViews)
        #self.setCentralWidget(self.p)


    def plotCurve(self, xVals, currentDict, colours, markers, parent):
        i=0
        for key, vals in currentDict.items():
            name = key + '-ions'
            scatter = pg.ScatterPlotItem(x=xVals, y=vals, symbol=markers[i],
                                         pen =pg.mkPen(color=colours[i], width=3),
                                         brush=(0,0,0,0), size=12, pxMode=True, name = name)
            curve = pg.PlotCurveItem(x=xVals, y=vals, pen=pg.mkPen(color=colours[i], width=3))
            parent.addItem(scatter)
            parent.addItem(curve)
            if parent != self.p:
                self.p.plotItem.legend.addItem(scatter, name)
            #self.graphWidget.plot(xVals, vals, pen=pen, )
            #self.p.plotItem.legend.addItem(i,key)
            i+=1

    def makeCustomMarker(self, char):
        mysymbol = QtGui.QPainterPath()
        mysymbol.addText(0, 0, QtGui.QFont(), char)
        br = mysymbol.boundingRect()
        scale = min(1. / br.width(), 1. / br.height())
        tr = QtGui.QTransform()
        tr.scale(scale, scale)
        tr.translate(-br.x() - br.width() / 2., -br.y() - br.height() / 2.)
        return tr.map(mysymbol)



    def updateViews(self):
        self.p2.setGeometry(self.p.getViewBox().sceneBoundingRect())
        self.p2.linkedViewChanged(self.p.getViewBox(), self.p2.XAxis)

        '''self.graphWidget = pg.PlotWidget(self)
        self.setCentralWidget(self.graphWidget)

        styles = {"black": "#f00", "font-size": "18px"}
        self.graphWidget.setLabel('left', yLabel1, **styles)
        self.graphWidget.setLabel('right',  yLabel2, **styles)
        self.graphWidget.setLabel("bottom", "cleavage site", **styles)
        self.graphWidget.setBackground('w')
        self.graphWidget.setXRange(0, len(sequence)+0.5, padding=0)
        self.graphWidget.setYRange(-0.01, 1.01, padding=0)

        self.legend = pg.LegendItem(offset=(0., .5), labelTextSize='12pt')
        self.legend.setParentItem(self.graphWidget.graphicsItem())
        colours = ['r', 'b', 'y', 'm', 'c', 'g']
        markers = ['o','t', 's', 'p','h', 'star', '+', 'd', 'x', 't1','t2', 't3']
        self.plot(forwardVals,markers,colours)
        self.plot(backwardVals,markers[::-1],colours[::-1])
        line = pg.InfiniteLine(pos=0,angle=0,pen=pg.mkPen(color='w', width=0),movable=False)
        self.graphWidget.addItem(line)
        sequMarkers = {}
        for bb in self._sequence:
            if bb not in sequMarkers.keys():
                sequMarkers[bb] = self.makeCustomMarker(bb)
        for i, bb in enumerate(self._sequence):
            scatter = pg.ScatterPlotItem(x=(i+0.5,),
                                     y=(0.01,), symbol=sequMarkers[bb],
                                     pen=pg.mkPen(color='k', width=0.1),
                                     size=10, pxMode=True)
            self.graphWidget.addItem(scatter)'''
        """for i, bb in enumerate(self._sequence):
            text2 = pg.TextItem(bb, anchor=(i+0.5, 0.0))
            text2.setParentItem(line)
        self.show()"""


def main():
    forwardVals = {'c':[i/7 for i in range(8)]}
    backwardVals = {'y':[1-i/7 for i in range(8)]}
    app = QtWidgets.QApplication(sys.argv)
    plotFact = PlotFactory(None)
    plotFact.showOccupancyPlot(['G','C','A','U','G','C','A','U'],forwardVals,backwardVals,1)
    #main.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
