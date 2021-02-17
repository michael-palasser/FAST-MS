from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
pg.setConfigOptions(antialias=True)
pg.setConfigOption('background', '#c7c7c7')
pg.setConfigOption('foreground', '#000000')
from pyqtgraph.ptime import time
app = QtGui.QApplication([])

p = pg.plot()
p.setXRange(0,10)
p.setYRange(-10,10)
p.setWindowTitle('Current-Voltage')
p.setLabel('bottom', 'Bias', units='V', **{'font-size':'20pt'})
p.getAxis('bottom').setPen(pg.mkPen(color='#000000', width=3))
p.setLabel('left', 'Current', units='A',
            color='#c4380d', **{'font-size':'20pt'})
p.getAxis('left').setPen(pg.mkPen(color='#c4380d', width=3))
curve = p.plot(x=[], y=[], pen=pg.mkPen(color='#c4380d'))
p.showAxis('right')
p.setLabel('right', 'Dynamic Resistance', units="<font>&Omega;</font>",
            color='#025b94', **{'font-size':'20pt'})
p.getAxis('right').setPen(pg.mkPen(color='#025b94', width=3))

p2 = pg.ViewBox()
p.scene().addItem(p2)
p.getAxis('right').linkToView(p2)
p2.setXLink(p)
p2.setYRange(-10,10)
p2.invertY()

curve2 = pg.PlotCurveItem(x=[i for i in range(10)],y= [i/2 for i in range(10)],pen=pg.mkPen(color='#025b94', width=1))
p2.addItem(curve2)
curve1 = pg.PlotCurveItem(x=[i for i in range(10)],y= [i/2+1 for i in range(10)],pen=pg.mkPen(color='#025b94', width=1))
p.addItem(curve1)

def updateViews():
    global p2
    p2.setGeometry(p.getViewBox().sceneBoundingRect())
    p2.linkedViewChanged(p.getViewBox(), p2.XAxis)

updateViews()
p.getViewBox().sigResized.connect(updateViews)


if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()