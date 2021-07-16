import numpy as np

from PyQt5 import QtGui
import pyqtgraph as pg


class PlotFactory(object):
    '''
    Factory class which creates PlotWindows showing either occupancies or charges per cleavage site
    '''
    def __init__(self, parent):
        self._parent = parent
        self._colours = ['r', 'm', 'y', 'c', 'g', 'b']

    def showOccupancyPlot(self, sequence, forwardVals, backwardVals, maxY):
        self.initiatePlot(sequence, forwardVals, backwardVals, maxY, self.formatForOccupancies)

    def showChargePlot(self, sequence, forwardVals, backwardVals, maxY, forwardVals2, backwardVals2):
        self.initiatePlot(sequence, forwardVals, backwardVals, abs(maxY), self.formatForCharges)
        self.plotMinMaxVals(forwardVals2, backwardVals2)


    def initiatePlot(self, sequence, forwardVals, backwardVals, maxY, func):
        '''
        Constructs the corresponding plots. Plot has 2 lines (2 axis) in forward and backward direction
        :param (list[str]) sequence: sequence of building blocks
        :param (dict[str,ndarray[float]]) forwardVals: dictionary of
            {fragment type: proportions [fragment number x proportion]} in forward direction (N-term./5')
        :param (dict[str,ndarray[float]]) backwardVals: dictionary of
            {fragment type: proportions [fragment number x proportion]} in backward direction (C-term./3')
        :param (float) maxY: max. y value
        :param (callable) func: method which formats the plot
        '''
        self._forwardVals = forwardVals
        self._backwardVals = backwardVals
        self._sequence = sequence
        self._maxY = maxY
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
        func()
        self.plot()
        self._plot1.resize(len(sequence) * 25 + 200, 400)
        self._plot2.resize(2000, 1000) #if too small the second graph will dissapear when scaling up

    def addSequence(self):
        '''
        Adds building block markers to the plot at the corresponding positions
        '''
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


    def makeCustomMarker(self, bb):
        '''
        Creates a new building block marker
        :param (str) bb: name of building block
        :return: marker
        '''
        mysymbol = QtGui.QPainterPath()
        mysymbol.addText(0, 0, QtGui.QFont(), bb)
        br = mysymbol.boundingRect()
        scale = min(1. / br.width(), 1. / br.height())
        tr = QtGui.QTransform()
        tr.scale(scale, scale)
        tr.translate(-br.x() - br.width() / 2., -br.y() - br.height() / 2.)
        return tr.map(mysymbol)



    def formatForCharges(self):
        '''
        Formats the plot if it's a charge plot
        '''
        self._plot1.setWindowTitle('Charge Distribution')
        yLabel = 'average charge '
        styles = {"black": "#f00", "font-size": "18px"}
        self._plot1.setLabel('left', yLabel + ','.join(self._forwardVals.keys()), **styles)
        self._plot1.setLabel('right', yLabel + ','.join(self._backwardVals.keys()), **styles)

    def formatForOccupancies(self):
        '''
        Formats the plot if it's an occupancy plot
        '''
        self._plot1.setWindowTitle('Occupancies')
        yLabel = 'occupancy '
        styles = {"black": "#f00", "font-size": "18px"}
        self._plot1.setLabel('left', yLabel + ','.join(self._forwardVals.keys()), **styles)
        self._plot1.setLabel('right', yLabel + ','.join(self._backwardVals.keys()), **styles)


    def plot(self):
        '''
        Plots the lines on the plot
        '''
        markers = ['t1', 'o', 's', 'p', 'h', 'star', 't2', 't3', '+', 'd', 'x','t']
        sequLength = len(self._sequence)
        self.plotCurve([i+1 for i in range(sequLength)], self._forwardVals, self._colours, markers, self._plot1)
        self.plotCurve([sequLength-i-1 for i in range(sequLength)], self._backwardVals, self._colours[::-1],
                       markers[::-1], self._plot2)
        self.updateViews()
        self._plot1.getViewBox().sigResized.connect(self.updateViews)


    def plotCurve(self, xVals, currentDict, colours, markers, parent):
        '''
        Plots a line on the plot
        :param (list[int]) xVals: cleavage site
        :param (dict[str,ndarray[float]]) currentDict: dictionary of
            {fragment type: proportions [fragment number x proportion]}
        :param (list[str]) colours: colour codes for the lines
        :param (list[str]) markers: marker codes for the lines
        :param parent:
        '''
        i=0
        for key, vals in currentDict.items():
            name = key + '-ions'
            if parent!=self._plot1:
                vals = [self._maxY-val for val in vals]
            scatter = pg.ScatterPlotItem(x=xVals, y=vals, symbol=markers[i],
                                         pen =pg.mkPen(color=colours[i], width=2),
                                         brush=(0,0,0,0), size=10, pxMode=True, name = name)
            curve = pg.PlotCurveItem(x=xVals, y=vals, pen=pg.mkPen(color=colours[i], width=2))
            self._plot1.addItem(scatter)
            self._plot1.addItem(curve)
            i+=1

    def plotMinMaxVals(self, forwardVals, backwardVals):
        '''
        Plots the minimum and maximum charge value for each cleavage site
        :param (dict[str:ndarray[float, float]]]) forwardVals: dictionary with min/max charges
            {fragment type: charge array[fragment number x (min.charge, max charge)]} in forward direction (N-term./5')
        :param (dict[str:ndarray[float, float]]]) backwardVals: dictionary with min/max charges
            {fragment type: charge array[fragment number x (min.charge, max charge)]} in backward direction (C-term./3')
        '''
        sequLength = len(self._sequence)
        self.plotVals([i+1 for i in range(sequLength)], forwardVals, self._colours, self._plot1)
        self.plotVals([sequLength-i-1 for i in range(sequLength)], backwardVals, self._colours[::-1], self._plot2)

    def plotVals(self, xVals, currentDict, colours, parent):
        '''
        Plots the corresponding values as scatter
        :param (list[int]) xVals: cleavage site
        :param (dict[str:ndarray[float, float]]]) currentDict: dictionary with min/max charges
            {fragment type: charge array[fragment number x (min.charge, max charge)]}
        :param (list[str]) colours: colour codes for the lines
        :param parent:
        '''
        i=0
        for key, vals in currentDict.items():
            marker = '+'
            if parent!=self._plot1:
                vals = np.array([self._maxY-val for val in vals])
                marker = 'x'
            self._plot1.addItem(pg.ScatterPlotItem(x=xVals, y=vals[:, 0], symbol=marker,
                                                   pen =pg.mkPen(color=colours[i], width=0.8), size=8, pxMode=True))
            self._plot1.addItem(pg.ScatterPlotItem(x=xVals, y=vals[:, 1], symbol=marker,
                                                   pen =pg.mkPen(color=colours[i], width=0.8), size=8, pxMode=True))
            i+=1



    def updateViews(self):
        '''
        Resets the plot window
        '''
        self._plot2.setGeometry(self._plot1.getViewBox().sceneBoundingRect())
        self._plot2.linkedViewChanged(self._plot1.getViewBox(), self._plot2.XAxis)
