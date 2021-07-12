import sys
import numpy as np

from PyQt5 import QtWidgets, QtGui
import pyqtgraph as pg


class PlotFactory(object):
    '''
    Factory class which creates PlotWindows showing either occupancies or charges per cleavage site
    '''
    def __init__(self, parent):
        self._parent = parent
        self._colours = ['r', 'm', 'y', 'c', 'g', 'b']
        '''self._colours = ['r', 'm', 'y', 'c', 'g', 'b']
        self._markers = ['o','t', 's', 'p','h', 'star', '+', 'd', 'x', 't1','t2', 't3']'''

    def showOccupancyPlot(self, sequence, forwardVals, backwardVals, maxY):
        self.initiatePlot(sequence, forwardVals, backwardVals, maxY, self.formatForOccupancies)

    def showChargePlot(self, sequence, forwardVals, backwardVals, maxY, forwardVals2, backwardVals2):
        self.initiatePlot(sequence, forwardVals, backwardVals, abs(maxY), self.formatForCharges)
        self.plotMinMaxVals(forwardVals2, backwardVals2)


    def initiatePlot(self, sequence, forwardVals, backwardVals, maxY, func):
        #self.plotWdw = QtWidgets.QMainWindow(self._parent)
        self._forwardVals = forwardVals
        self._backwardVals = backwardVals
        self._sequence = sequence
        self._maxY = maxY
        #self._translate = QtCore.QCoreApplication.translate
        #self.plotWdw.resize(len(sequence) * 30 + 200, 400)
        self._plot1 = pg.plot()
        self._plot1.addLegend(labelTextSize='14pt')
        self._plot1.setBackground('w')
        self._plot1.showAxis('right')
        self._plot2 = pg.ViewBox()
        self._plot1.scene().addItem(self._plot2)
        self._plot1.getAxis('right').linkToView(self._plot2)
        self._plot2.setXLink(self._plot1)
        self._plot2.setYLink(self._plot1)
        styles = {"black": "#f00", "font-size": "20px"}
        self._plot1.setLabel('bottom', 'cleavage site', **styles)
        yRange = [-self._maxY*0.05,self._maxY*1.05]
        self._plot1.setXRange(0.02, len(self._sequence) + 0.02)
        self._plot1.plotItem.vb.setLimits(xMin=0, xMax=len(self._sequence) + 0.01, yMin=yRange[0], yMax=yRange[1])
        self._plot2.setLimits(xMin=0, xMax=len(self._sequence) + 0.01, yMin=yRange[0], yMax=yRange[1])
        self._plot1.setRange(yRange=yRange, padding=0)
        self._plot2.setRange(yRange=yRange, padding=0)
        self._plot2.invertY()
        self.addSequence()
        #self.legend = pg.LegendItem(offset=(0., .5), labelTextSize='12pt')
        #self.legend.setParentItem(self.p)
        func()
        self.plot()
        self._plot1.resize(len(sequence) * 25 + 200, 400)
        self._plot2.resize(2000, 1000) #if too small the second graph will dissapear when scaling up
        #self.p = self.makeAxis(yLabel,forwardVals)

    def addSequence(self):
        line = pg.InfiniteLine(pos=0,angle=0,pen=pg.mkPen(color='w', width=0),movable=False)
        self._plot1.addItem(line)
        sequMarkers = {}
        for bb in self._sequence:
            if bb not in sequMarkers.keys():
                sequMarkers[bb] = self.makeCustomMarker(bb)
        for i, bb in enumerate(self._sequence):
            scatter = pg.ScatterPlotItem(x=(i+0.5,),y=(0,), symbol=sequMarkers[bb],
                                         pen=pg.mkPen(color='k', width=0.1), size=10, pxMode=True)
            self._plot1.addItem(scatter)

    def formatForCharges(self):
        self._plot1.setWindowTitle('Charge Distribution')
        yLabel = 'average _charge '
        styles = {"black": "#f00", "font-size": "18px"}
        self._plot1.setLabel('left', yLabel + ','.join(self._forwardVals.keys()), **styles)
        self._plot1.setLabel('right', yLabel + ','.join(self._backwardVals.keys()), **styles)

    def formatForOccupancies(self):
        self._plot1.setWindowTitle('Occupancies')
        yLabel = 'occupancy '
        styles = {"black": "#f00", "font-size": "18px"}
        #self.p.setLabel('left', yLabel+','.join(self._forwardVals.keys()), units='%', **styles)
        #self.p.setLabel('right', yLabel+','.join(self._backwardVals.keys()), units='%', **styles)
        self._plot1.setLabel('left', yLabel + ','.join(self._forwardVals.keys()), **styles)
        self._plot1.setLabel('right', yLabel + ','.join(self._backwardVals.keys()), **styles)


    def plot(self):
        markers = ['t1', 'o', 's', 'p', 'h', 'star', 't2', 't3', '+', 'd', 'x','t']
        sequLength = len(self._sequence)
        #xVals = [i+1 for i in range(sequLength)]
        self.plotCurve([i+1 for i in range(sequLength)], self._forwardVals, self._colours, markers, self._plot1)
        self.plotCurve([sequLength-i-1 for i in range(sequLength)], self._backwardVals, self._colours[::-1],
                       markers[::-1], self._plot2)
        self.updateViews()
        self._plot1.getViewBox().sigResized.connect(self.updateViews)
        #self.setCentralWidget(self.p)


    def plotCurve(self, xVals, currentDict, colours, markers, parent):
        i=0
        for key, vals in currentDict.items():
            name = key + '-ions'
            if parent!=self._plot1:
                vals = [self._maxY-val for val in vals]
            scatter = pg.ScatterPlotItem(x=xVals, y=vals, symbol=markers[i],
                                         pen =pg.mkPen(color=colours[i], width=2),
                                         brush=(0,0,0,0), size=10, pxMode=True, name = name)
            curve = pg.PlotCurveItem(x=xVals, y=vals, pen=pg.mkPen(color=colours[i], width=2))
            #parent.addItem(scatter)
           # parent.addItem(curve)
            self._plot1.addItem(scatter)
            self._plot1.addItem(curve)
            #if parent != self.p:
            #    self.p.plotItem.legend.addItem(scatter, name)
            #self.graphWidget.plot(xVals, vals, pen=pen, )
            #self.p.plotItem.legend.addItem(i,key)
            i+=1

    def plotMinMaxVals(self, forwardVals, backwardVals):
        sequLength = len(self._sequence)

        self.plotVals([i+1 for i in range(sequLength)], forwardVals, self._colours, self._plot1)
        self.plotVals([sequLength-i-1 for i in range(sequLength)], backwardVals, self._colours[::-1], self._plot2)

    def plotVals(self, xVals, currentDict, colours, parent):
        i=0
        for key, vals in currentDict.items():
            #name = key + '-ions'
            marker = '+'
            if parent!=self._plot1:
                vals = np.array([self._maxY-val for val in vals])
                marker = 'x'
            #print(key, vals)
            #[print(key,xVal,yVal) for xVal,yVal in zip(xVals,vals)]
            self._plot1.addItem(pg.ScatterPlotItem(x=xVals, y=vals[:, 0], symbol=marker,
                                                   pen =pg.mkPen(color=colours[i], width=0.8), size=8, pxMode=True))
            self._plot1.addItem(pg.ScatterPlotItem(x=xVals, y=vals[:, 1], symbol=marker,
                                                   pen =pg.mkPen(color=colours[i], width=0.8), size=8, pxMode=True))
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
        self._plot2.setGeometry(self._plot1.getViewBox().sceneBoundingRect())
        self._plot2.linkedViewChanged(self._plot1.getViewBox(), self._plot2.XAxis)

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
