import sys

import numpy as np
from PyQt5.QtWidgets import QApplication
from matplotlib import pyplot as plt
from PyQt5 import QtGui
import pyqtgraph as pg
from matplotlib.ticker import MultipleLocator

from src.resources import DEVELOP, INTERN

SEQUENCE = True

class PlotFactory(object):
    '''
    Factory class which creates PlotWindows showing either occupancies or charges per cleavage site
    '''
    def __init__(self, parent):
        self._parent = parent
        self._colours = ['r', 'm', 'y', 'c', 'g', 'b']
        if INTERN:
            """self._colours = list({'tab:red':'#d62728', 'tab:orange':'#ff7f0e',
                             'tab:purple':'#9467bd', 'tab:brown':'#8c564b',
                             'gold':'#dbb40c', 'm':'m', 'darkred':'#840000',
                             'limegreen':'#aaff32','tab:gray':'#7f7f7f',
                             'tab:olive':'#bcbd22', 'tab:cyan':'#17becf',
                             'tab:green':'#2ca02c', 'royalblue':'#0504aa'}.values())"""
        self._colours = list({'tab:red': '#d62728', 'royalblue': '#4169e1',
                              'tab:green': '#2ca02c', 'tab:orange': '#ff7f0e',
                              'tab:purple': '#9467bd', 'tab:cyan': '#17becf',
                              'tab:brown': '#8c564b', 'tab:olive': '#bcbd22',
                              'tab:gray': '#7f7f7f', 'm': 'm', 'gold': '#dbb40c',
                              'darkred': '#840000', 'limegreen': '#aaff32'}.values())

        if DEVELOP:
            self._fontsize = 10
        else:
            self._fontsize = 12

    def showOccupancyPlot(self, sequence, forwardVals, backwardVals, maxY, modification):
        self.initiatePlot(sequence, forwardVals, backwardVals, maxY, lambda: self.formatForOccupancies(modification, maxY))
        #self.initiateAbsPlot(sequence, absVals, maxY, 'Abs. Occupancies '+modification)
        return self._plot1

    def showChargePlot(self, sequence, forwardVals, backwardVals, maxY, forwardVals2, backwardVals2):
        self.initiatePlot(sequence, forwardVals, backwardVals, abs(maxY), self.formatForCharges)
        self.plotMinMaxVals(forwardVals2, backwardVals2)
        return self._plot1

    def getFontSizeString(self):
        return str(self._fontsize)+'pt'

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
        self._plot1.addLegend(labelTextSize=self.getFontSizeString(), labelTextColor="k")
        self._plot1.setBackground('w')
        self._plot1.showAxis('right')
        self._plot2 = pg.ViewBox()
        self._plot1.scene().addItem(self._plot2)
        self._plot1.getAxis('right').linkToView(self._plot2)
        self._plot2.setXLink(self._plot1)
        self._plot2.setYLink(self._plot1)
        styles = {"black": "#f00", "font-size": self.getFontSizeString()}
        self._plot1.setLabel('bottom', 'cleavage site', **styles)

        for axisName in ("left", "bottom", "right"):
            font=QtGui.QFont()
            font.setPointSize(10)
            axis = self._plot1.getAxis(axisName)
            axis.setStyle(tickFont=font)
            axis.setPen(pg.mkPen(color="k", width=0.5))
            axis.setTextPen('k')
            if axisName=="bottom":
                major=2
                if len(sequence)>30:
                    major = 5
                axis.setTickSpacing(major=major, minor=1)
        yRange = [-self._maxY*0.05,self._maxY*1.05]
        self._plot1.setXRange(0, len(self._sequence),padding=0)
        self._plot1.plotItem.vb.setLimits(xMin=0, xMax=len(self._sequence) + 0.01, yMin=yRange[0], yMax=yRange[1])
        self._plot2.setLimits(xMin=0, xMax=len(self._sequence) + 0.01, yMin=yRange[0], yMax=yRange[1])
        self._plot1.setRange(yRange=yRange, padding=0)
        self._plot2.setRange(yRange=yRange, padding=0)
        self._plot2.invertY()
        if SEQUENCE:
            self.addSequence(self._plot1)
        func()
        self.plot()
        if DEVELOP:
            factor = self._fontsize/10
            self._plot1.resize(int(700*factor), int(350*factor))
        else:
            self._plot1.resize(len(sequence) * 20 + 150, 400)
        self._plot2.resize(2000, 1000) #if too small the second graph will dissapear when scaling up

    def addSequence(self, plot):
        '''
        Adds building block markers to the plot at the corresponding positions
        '''
        line = pg.InfiniteLine(pos=0,angle=0,pen=pg.mkPen(color='w', width=0),movable=False)
        plot.addItem(line)
        sequMarkers = {}
        for bb in self._sequence:
            if bb not in sequMarkers.keys():
                sequMarkers[bb] = self.makeCustomMarker(bb)
        for i, bb in enumerate(self._sequence):
            scatter = pg.ScatterPlotItem(x=(i+0.5,),y=(0,), symbol=sequMarkers[bb],
                                         pen=pg.mkPen(color='k', width=0.1), size=self._fontsize*1.4, pxMode=True)
            plot.addItem(scatter)


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
        styles = {"black": "#f00", "font-size": self.getFontSizeString()}
        self._plot1.setLabel('left', yLabel + ','.join(self._forwardVals.keys()), **styles)
        self._plot1.setLabel('right', yLabel + ','.join(self._backwardVals.keys()), **styles)

    def formatForOccupancies(self, modification, maxY):
        '''
        Formats the plot if it's an occupancy plot
        '''
        self._plot1.setWindowTitle('Localise ' +modification)
        #yLabel = '% '+modification + ' ('
        yLabel = modification + ' ('
        styles = {"black": "#f00", "font-size": self.getFontSizeString()}
        self._plot1.setLabel('left', yLabel + ','.join(self._forwardVals.keys()) + ')', **styles)
        self._plot1.setLabel('right', yLabel + ','.join(self._backwardVals.keys()) + ')', **styles)
        for axisName in ("left", "right"):
            font=QtGui.QFont()
            font.setPointSize(10)
            axis = self._plot1.getAxis(axisName)
            major = 0.2
            if maxY > 1:
                major = 0.5
            axis.setTickSpacing(major=major, minor=major / 2)


    def plot(self):
        '''
        Plots the lines on the plot
        '''
        markers = ['t1', 'o', 's', 'p', 'h', 'star', 't2', 't3', '+', 'd', 'x','t']
        sequLength = len(self._sequence)
        self.plotCurve([i+1 for i in range(sequLength)], self._forwardVals, self._colours, markers, self._plot1)
        self.plotCurve([sequLength-i-1 for i in range(sequLength)], self._backwardVals, self._colours[len(self._forwardVals.keys()):], #self._colours[::-1],
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
            name = key + ' fragments'
            if parent!=self._plot1:
                vals = [self._maxY-val for val in vals]
            #newXVals, newVals, connected = self.removeNANVals(xVals,vals)
            connected = self.removeNANVals(xVals,vals)
            #curve = pg.PlotCurveItem(x=newXVals,y=newVals,pen=pg.mkPen(color=colours[i], width=2))
            """scatter = pg.ScatterPlotItem(x=newXVals, y=newVals, symbol=markers[i],
                                         pen =pg.mkPen(color=colours[i], width=2),
                                         brush=(0,0,0,0), size=10, pxMode=True, name = name)"""
            plotData = pg.PlotDataItem(x=xVals, y=vals, symbol=markers[i],
                                       pen =pg.mkPen(color=colours[i], width=2),
                                       symbolPen=pg.mkPen(color=colours[i], width=2),
                                       symbolBrush=(0,0,0,0), symbolSize=10, pxMode=True, name = name,
                                       connect=connected)
            #newXVals, newVals = self.removeNANVals(xVals,vals)
            self._plot1.addItem(plotData)
            #self._plot1.addItem(scatter)
            i+=1

    def removeNANVals(self, xVals, vals):
        '''
        PlotCurveItem does not like nan values
        '''
        connected = []
        #newXVals, newVals, connected = [],[],[]
        for xVal,val in zip(xVals,vals):
            if not np.isnan(val):
                #newXVals.append(xVal)
                #newVals.append(val)
                connected.append(1)
            else:
                #newXVals.append(xVal)
                #newVals.append(val)
                connected.append(0)
        return np.array(connected)#newXVals, newVals, np.array(connected)


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



    """def initiateAbsPlot(self, sequence, absVals, maxY, title):
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
        self._absVals = absVals
        self._sequence = sequence
        sequLength = len(sequence)
        self._plot3 = pg.plot()
        self._plot3.addLegend(labelTextSize='14pt')
        self._plot3.setBackground('w')
        self._plot3.showAxis('right')
        styles = {"black": "#f00", "font-size": "20px"}
        self._plot3.setLabel('bottom', 'cleavage site', **styles)
        yRange = [-maxY*0.05,maxY*1.05]
        self._plot3.setXRange(0.02, sequLength + 0.02)
        self._plot3.plotItem.vb.setLimits(xMin=0, xMax=len(self._sequence) + 0.01, yMin=yRange[0], yMax=yRange[1])
        self._plot3.setRange(yRange=yRange, padding=0)
        self.addSequence(self._plot3)
        self._plot3.setWindowTitle(title)
        #self._plot3.setWindowTitle('Fragmentation Efficiencies')
        yLabel = '∑ rel. abundances'
        styles = {"black": "#f00", "font-size": "18px"}
        self._plot3.setLabel('left', yLabel + ','.join(self._absVals.keys()) + ')', **styles)
        self.plotBars([i+1 for i in range(sequLength)], self._absVals, self._colours)
        self._plot3.resize(len(sequence) * 25 + 200, 400)


    def plotBars(self, xVals, currentDict, colours):
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
            if vals.shape[0] == 1:
                self._plot3.addItem(bars = pg.BarGraphItem(x=xVals, height=vals, width=0.5, brush=colours[i], name=name))
            else:
                self._plot3.addItem(pg.BarGraphItem(x=xVals, height=vals[:,0], width=0.5, brush=colours[i], name=name))
                self._plot3.addItem(pg.BarGraphItem(x=xVals, height=vals[:,1], width=0.5, brush=colours[i], name=name))
            i+=1"""


def plotBars(sequence, values, headers, title, occup=False):
    '''
    Plots the relative abundances per cleavage site for every fragment type
    :param (list[str]) sequence:
    :param (ndarray[float]) values:
    :param headers: header for each column of values
    :param title:
    :param occup: True for occupancy plot
    :return:
    '''
    #sequLength = len(sequence)
    if DEVELOP:
        plt.rcParams.update({'font.size': 10})
    else:
        plt.rcParams.update({'font.size': 12})
    colours = ['tab:red','royalblue','tab:green', 'tab:orange', 'tab:purple', 'tab:cyan', 'tab:brown', 'tab:olive',
               'tab:gray', 'm','gold','darkred','limegreen','gold']
    nrCols = len(headers)
    nrRows = len(values)
    xVals = np.arange(1,nrRows+1)
    width = 0.8  # the width of the bars: can also be len(x) sequence

    fig, ax = plt.subplots()#figsize=(50,nrRows*10+50))
    bottom=np.zeros(nrRows)

    size =nrRows/5+4, 4
    if DEVELOP:
        toInch = 2.54/2
        size = 7/toInch, 3.8/toInch
    fig.set_figwidth(size[0])
    fig.set_figheight(size[1])

    for i in range(nrCols):
        #index=nrCols-i-1
        if occup:
            if not i%2:
                ax.bar(xVals, values[:,i], width, bottom= bottom, label=headers[i], color='w',
                       edgecolor=colours[int(i/2)], linewidth=0.7)
            else:
                ax.bar(xVals, values[:,i], width, bottom= bottom, label=headers[i], color=colours[int(i/2)],
                       edgecolor=colours[int(i/2)], linewidth=0.7)
        else:
            ax.bar(xVals, values[:,i], width, bottom= bottom, label=headers[i], color=colours[i])
        bottom += values[:,i]
    sequColour = 'black'
    '''if occup:
        sequColour = 'saddlebrown'''
    if SEQUENCE:
        for i,bb in enumerate(sequence):
            plt.text(x=i+0.5, y=0, s=bb, fontsize=10, c=sequColour, ha='center')
            #plt.text(x=(i+0.5)/sequLength, y=0, s=bb, fontsize=10, c=sequColour, ha='center', transform = ax.transAxes)
    ax.set_ylabel('rel. abundance /a.u.')
    ax.set_xlabel('cleavage site')
    ax.xaxis.set_major_locator(MultipleLocator(5))
    #ax.xaxis.set_major_formatter('{x:.0f}')
    ax.xaxis.set_minor_locator(MultipleLocator(1))
    ax.ticklabel_format(axis="y", style="sci", scilimits=(0,0))
    plt.grid(axis = 'y',linestyle = '--', linewidth = 0.4)
    ax.set_title(title)
    leg = ax.legend()
    if leg:
        leg.set_draggable(True)
    ax.set_xlim([0, nrRows+1])
    ax.set_ylim([0, np.max(np.sum(values,axis=1))*1.1])
    plt.tight_layout(pad=0.8)
    plt.show()

#Test
if __name__ == '__main__':
    arr = np.zeros((26,2))
    for i in range(26):
        for j in range(2):
            arr[i,j] = np.random.randint(100000)
    sequ = list('GGCUGCUUGUCCUUUAAUGGUCCAGUC')
    #plotBars(sequ, arr, ['c','y'], '')
    arr = np.zeros((26,4))
    for i in range(26):
        for j in range(4):
            arr[i,j] = np.random.randint(100000)
    #plotBars(sequ, arr, ['c','c+CMCT','y','y+CMCT'], 'hey', False)

    app = QApplication(sys.argv)
    plotFactory = PlotFactory(None)
    forwardVals = {'c':np.random.rand(len(sequ))}
    backwardVals =  {'y':np.random.rand(len(sequ))}

    #plotFactory.showOccupancyPlot(sequ, forwardVals, backwardVals,1, 'CMCT')
    sequ = sequ[:15]
    forwardVals={'c': np.array([np.nan, 0.62842433, 0.55673973, np.nan, 0.52191535,
                 0.81935084, 0.69020276, 0.75760611, 1., 1.,
                 0.68116389, 1., 1., 0.5610877, np.nan])}
    backwardVals= {'y': np.array([np.nan, 0., 0., 0., 0.,
                 0., 0., 0., 0., 0.,
                 0., 0.08697064, 0.09865665, 0., np.nan])}
    plot = plotFactory.showOccupancyPlot(sequ, forwardVals, backwardVals,1, 'CMCT')
    plotBars(sequ, arr, ['c','y'], '')

    sys.exit(app.exec_())