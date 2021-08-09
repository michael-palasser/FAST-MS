import sys
from copy import deepcopy

import numpy as np
import matplotlib
from matplotlib import pyplot as plt
import matplotlib.ticker as mticker


from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import Qt, QVariant, QCoreApplication
from PyQt5.QtWidgets import QApplication
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.patches import Rectangle

from src.gui.GUI_functions import connectTable, showOptions, makeLabelInputWidget, createComboBox
from src.gui.tableviews.TableModels import AbstractTableModel


class SequCovPlotTableModel(AbstractTableModel):
    '''
    TableModel for a QTableView in SequCovWidget which shows if a fragment was found at a cleavage site
    '''
    def __init__(self, data, headers):
        super(SequCovPlotTableModel, self).__init__(data, (), headers)

    def data(self, index, role):
        '''
        Overwrites the data method of AbstractTableModel to correctly format each value
        '''
        if index.isValid():
            if role == Qt.DisplayRole:
                return self._data[index.row()][index.column()]
        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        if role == Qt.BackgroundRole:
            row,col = index.row(), index.column()
            if (row!=0) and (row!=len(self._data)-1) and (col!=0):
                if self._data[row][col]==1:
                    return QVariant(QtGui.QColor(Qt.green))
                elif self._data[row][col]==0:
                    return QVariant(QtGui.QColor(Qt.red))


class SequCovTableModel(AbstractTableModel):
    '''
    TableModel for a QTableView in SequCovWidget which shows the sequence coverage for each fragment type
    '''
    def __init__(self, data):
        super(SequCovTableModel, self).__init__(data, (), ('fragm. type', 'sequ.cov. /%'))

    def data(self, index, role):
        '''
        Overwrites the data method of AbstractTableModel to correctly format each value
        '''
        if index.isValid():
            if role == Qt.DisplayRole:
                col = index.column()
                item = self._data[index.row()][col]
                if col == 0:
                    return item
                # print(item)
                return '{:2.1f}'.format(item)
        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter


class SequCovWidget(QtWidgets.QWidget):
    '''
    Widget which shows all sequence coverage details
    '''
    def __init__(self, values, sequence, coveragesForw, coveragesBackw, globalData):
        super().__init__(parent=None)
        self._fragments = {}
        self._translate = QCoreApplication.translate
        self._coveragesForw = coveragesForw
        self._coveragesBackw = coveragesBackw
        self._globalData = globalData
        self._sequLength = len(sequence)
        verticalLayout = QtWidgets.QVBoxLayout(self)
        model = SequCovTableModel(values)
        table = QtWidgets.QTableView(self)
        table.setModel(model)
        #table.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        table.resizeColumnsToContents()
        table.setSortingEnabled(True)
        [table.setRowHeight(i,23) for i in range(len(values))]
        table.setMinimumHeight((len(values)+1)*23)
        connectTable(table,showOptions)
        verticalLayout.addWidget(table)
        all = deepcopy(coveragesForw)
        all.update(coveragesBackw)
        coverageData = self.addCleavageSites([[key] + list(val) for key,val in all.items()])
        verticalLayout.addWidget(self.makeCoverageTable(coverageData, ['fragm.'] + sequence))
        #verticalLayout.addWidget(self.makeCoverageTable(globalData, ['direction'] + sequence))
        width = 10
        if self._sequLength>200:
            width = 30
        elif self._sequLength>100:
            width = 20
        elif self._sequLength>50:
            width = 15
        self._lineWidth = QtWidgets.QSpinBox()
        self._lineWidth.setValue(width)
        self._lineWidth.setMaximum(999)
        updateBtn = QtWidgets.QPushButton()
        updateBtn.setText('Update')
        widg, _ = makeLabelInputWidget(self, 'nr. of res. per line:', self._lineWidth, updateBtn)
        verticalLayout.addWidget(widg)

        self._inputWidget = QtWidgets.QWidget(self)
        self._gridLayout = QtWidgets.QGridLayout(self._inputWidget)
        self.fillGrid('total', 0, True)
        for i,key in enumerate(all.keys()):
            self.fillGrid(key, i+1)
        verticalLayout.addWidget(self._inputWidget)
        self.setObjectName('Sequence Coverage')
        self.setWindowTitle(self._translate(self.objectName(), self.objectName()))
        self.show()
        self._sequPlot = SequenceCoveragePlot(sequence, globalData[:,0].reshape((self._sequLength,1)),
                                              globalData[:,1].reshape((self._sequLength,1)), width)
        updateBtn.clicked.connect(self.updatePlot)

    def fillGrid(self, type, row, checked=False):
        label = QtWidgets.QLabel(self._inputWidget)
        label.setText(self._translate(self._inputWidget.objectName(), type))
        tickBox = QtWidgets.QCheckBox(self._inputWidget)
        tickBox.setChecked(checked)
        comboBox = createComboBox(self._inputWidget, ['red','blue','green', 'orange', 'brown', 'purple'])
        self._gridLayout.addWidget(label, row, 0)
        self._gridLayout.addWidget(tickBox, row, 1)
        self._gridLayout.addWidget(comboBox, row, 2)
        self._fragments[type] = (tickBox,comboBox)

    def makeCoverageTable(self, data, headers):
        model = SequCovPlotTableModel(data, headers)
        table = QtWidgets.QTableView(self)
        # self._table.setSortingEnabled(True)
        table.setModel(model)
        #table.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        table.resizeColumnsToContents()
        table.setColumnWidth(0,70)
        table.resizeRowsToContents()
        connectTable(table,showOptions)
        #table.resize(70+len(data[0])*table.columnWidth(1), (len(data)+1)*table.rowHeight(0))
        return table


    def addCleavageSites(self, data):
        newData = [[''] + [str(i + 1) for i in range(self._sequLength)]]
        newData += data
        newData.append([''] + [str(self._sequLength - i) for i in range(self._sequLength)])
        return newData


    def updatePlot(self):
        forward,backward =[],[]
        forwardC,backwardC =[],[]
        if self._fragments['total'][0].isChecked():
            forward.append(self._globalData[:,0])
            colour = self._fragments['total'][1].currentText()
            forwardC.append(colour)
            backwardC.append(colour)
            backward.append(self._globalData[:,1])
        for key, tup in self._fragments.items():
            if key in self._coveragesForw.keys():
                if tup[0].isChecked():
                    forward.append(self._coveragesForw[key])
                    forwardC.append(tup[1].currentText())
            elif key in self._coveragesBackw.keys():
                if tup[0].isChecked():
                    backward.append(self._coveragesBackw[key])
                    backwardC.append(tup[1].currentText())
        forward2,backward2 = [],[]
        for i in range(self._sequLength):
            forward2.append([arr[i] for arr in forward])
            backward2.append([arr[i] for arr in backward])
        print(self._coveragesForw.keys())
        self._sequPlot.makePlot(forward2, backward2,self._lineWidth.value(), forwardC,backwardC)
        self._sequPlot.draw()
        self.show()


class SequenceCoveragePlot(FigureCanvasQTAgg):
    '''
    Matplotlib plot which shows the sequence coverages
    '''
    def __init__(self, sequence, coveragesForward, coverageBackward, width):
        self._sequence= sequence
        self._coveragesForward = coveragesForward
        self._coverageBackward = coverageBackward
        self.makePlot(coveragesForward, coverageBackward, width)
        super(SequenceCoveragePlot, self).__init__(self._fig)

    def makePlot(self, coveragesForward, coveragesBackward, lineWidth, coloursF=['red'],coloursB=['red']):
        rows = int(len(self._sequence) / lineWidth)+1
        step_x = 1/(lineWidth+1)
        step_y = 1/(2*rows)
        print('rows', rows, len(self._sequence),step_y)
        self._fig = plt.figure(figsize=(lineWidth,rows+0))
        matplotlib.rcParams.update({'font.size': 15})
        ax = plt.subplot(111)
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.xaxis.set_major_locator(mticker.LinearLocator(0))
        ax.yaxis.set_major_locator(mticker.LinearLocator(0))
        ax.xaxis.set_tick_params(width=3, top = False, direction='out')
        ax.xaxis.set_tick_params(width=3, bottom = False, direction='out')
        ax.yaxis.set_tick_params(width=3, left = False, direction='out')
        ax.yaxis.set_tick_params(width=3, right = False, direction='out')
        xPos=step_x/2
        line=step_y
        counter = 1
        plt.text(x=-step_x*0.6, y=1-line, s=str(counter), fontsize=12)
        #size = 0.01
        for i,bb in enumerate(self._sequence):
            plt.text(x=xPos, y=1-line, s=bb, fontsize=20)
            for j,coverageForward in enumerate(coveragesForward[i]):
                if coverageForward and not np.isnan(coverageForward):
                    yPos_j=1-line+step_y*0.49+(len(coveragesForward[i])-j-1)*step_y*0.2
                    plt.text(x=xPos+step_x*0.6443, y=yPos_j, s='L', ha='right', c=coloursF[j],rotation=180)
                    plt.text(x=xPos+step_x*0.62, y=1-line+step_y*0, s='I', ha='left', c=coloursF[-1])
            counter+=1
            if not (i+1)%lineWidth:
                line+=2*step_y
                plt.text(x=-step_x*0.6, y=1-line, s=str(counter), fontsize=10)
                xPos=step_x/2
            if i != (len(self._sequence) - 1):
                for j,coverageBackward in enumerate(coveragesBackward[i+1]):
                    if coverageBackward and not np.isnan(coverageBackward):
                        yPos_j=1-line-step_y*0.3-(len(coveragesForward[i])-j-1)*step_y*0.2
                        plt.text(x=xPos+step_x*0.62, y=yPos_j, s='L', ha='left', c=coloursB[j])
                        #if (not coveragesForward[i]) or (xPos==step_x/2):
                        plt.text(x=xPos+step_x*0.62, y=1-line+step_y*0, s='I', ha='left', c=coloursB[-1])
            if (i+1)%lineWidth:
                xPos+=step_x
        plt.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    sequ = list('GGCUGCUUGUCCUUUAAUGGUCCAGUC')
    overall = [(key,val*100) for key,val in
               {'a': 0.7692307692307693, 'c': 0.9230769230769231, 'w': 0.7692307692307693, 'y': 0.9230769230769231, 'allForward': 0.9615384615384616, 'allBackward': 0.9230769230769231, 'all': 0.9259259259259259}.items()]
    '''gui = SequCovWidget( overall,
                         sequ, {'a': np.array([0., 1., 0., 1., 1., 1., 0., 1., 1., 1., 0., 0., 1., 0., 1., 1., 1.,
       1., 1., 1., 1., 1., 1., 1., 1., 1., np.nan]), 'c': np.array([0., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
       1., 1., 1., 1., 1., 0., 1., 1., 1.,np.nan])}, {'w': np.array([np.nan,1., 1., 0., 0., 1., 1., 0., 1., 1., 0., 1., 1., 1., 1., 1., 1., 1.,
       0., 1., 1., 1., 1., 1., 1., 1., 0.]), 'y': np.array([np.nan,1., 1., 1., 1., 1., 1., 1., 1., 1., 0., 1., 1., 1., 1., 1., 1., 1.,
       1., 1., 1., 1., 1., 1., 1., 1., 0.])},np.array([(val1,val2) for val1,val2 in zip(np.array([0., 1., 0., 1., 1., 1., 0., 1., 1., 1., 0., 0., 1., 0., 1., 1., 1.,
                                            1., 1., 1., 1., 1., 1., 1., 1., 1., np.nan]),np.array([np.nan,1., 1., 1., 1., 1., 1., 1., 1., 1., 0., 1., 1., 1., 1., 1., 1., 1.,
                                            1., 1., 1., 1., 1., 1., 1., 1., 0.]))]))
    '''
    sequ = list('GGCUGCUUGUCCUUUAAUGGUCCAGUC')*10
    sequLength = len(sequ)
    sequPlot = SequenceCoveragePlot(sequ, np.ones((sequLength,1)),
                                          np.ones((sequLength,1)), 20)
    sys.exit(app.exec_())