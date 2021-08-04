import sys
import numpy as np
import matplotlib
from matplotlib import pyplot as plt
import matplotlib.ticker as mticker


from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import Qt, QVariant, QCoreApplication
from PyQt5.QtWidgets import QApplication
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

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
    def __init__(self, values, sequence, fragmentData, globalData):
        super().__init__(parent=None)
        self._globalData = globalData
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

        verticalLayout.addWidget(self.makeCoverageTable(fragmentData, ['fragm.'] + sequence))
        #verticalLayout.addWidget(self.makeCoverageTable(globalData, ['direction'] + sequence))

        width = 10
        if len(sequence)>200:
            width = 30
        elif len(sequence)>100:
            width = 20
        elif len(sequence)>50:
            width = 15
        self._lineWidth = QtWidgets.QSpinBox()
        self._lineWidth.setValue(width)
        self._lineWidth.setMaximum(999)
        widg, _ = makeLabelInputWidget(self, 'nr. of res. per line:', self._lineWidth)
        verticalLayout.addWidget(widg)
        self._sequPlot = SequenceCoveragePlot(sequence, globalData[:][0], globalData[:][1], width)
        verticalLayout.addWidget(self._sequPlot)
        self._lineWidth.valueChanged.connect(self.updatePlot)

        self._translate = QCoreApplication.translate
        self.setObjectName('Sequence Coverage')
        self.setWindowTitle(self._translate(self.objectName(), self.objectName()))
        self.show()

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

    def updatePlot(self):
        self._sequPlot.makePlot(self._globalData[:][0], self._globalData[:][1],self._lineWidth.value())
        self.show()


def processCoverageData(sequ, dataDict):
    sequLength = len(sequ)
    data = [[''] + [str(i + 1) for i in range(sequLength)]]
    for key, line in dataDict.items():
        data.append([key] + list(line))
    data.append([''] + [str(sequLength - i) for i in range(sequLength)])
    return data


class SequenceCoveragePlot(FigureCanvasQTAgg):
    def __init__(self, sequence, coveragesForward, coverageBackward, width):
        self._sequence= sequence
        self._coveragesForward = coveragesForward
        self._coverageBackward = coverageBackward

        self.makePlot(coveragesForward, coverageBackward, width)
        super(SequenceCoveragePlot, self).__init__(self._fig)

    def makePlot(self, coveragesForward, coverageBackward, lineWidth):
        rows = int(len(self._sequence) / lineWidth)+1
        step_x = 1/(lineWidth)
        step_y = 1/(rows+1)

        self._fig = plt.figure(figsize=(lineWidth/1.5,rows))
        matplotlib.rcParams.update({'font.size': 20})
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

        xPos=0
        line=0
        counter = 1
        plt.text(x=-0.1, y=1, s=str(counter), fontsize=12)
        for i,bb in enumerate(self._sequence):
            plt.text(x=xPos, y=1-line, s=bb)
            xPos+=step_x
            if coveragesForward[i]:
                plt.text(x=xPos-step_x*0.343, y=1-line+step_y*0.49, s='L', fontsize=15, ha='right', c='red',rotation=180)
                plt.text(x=xPos-step_x*0.38, y=1-line+step_y*0, s='I', fontsize=15, ha='left', c='red')
            counter+=1
            if not (i+1)%lineWidth:
                line+=2*step_y
                plt.text(x=-0.1, y=1-line, s=str(counter), fontsize=10)
                xPos=0
            if (i!=len(self._sequence)-1) and coverageBackward[i+1]:
                plt.text(x=xPos-step_x*0.38, y=1-line-step_y*0.3, s='L', fontsize=15, ha='left', c='red',)
                if (not coveragesForward[i]) or xPos==0:
                    plt.text(x=xPos-step_x*0.38, y=1-line+step_y*0, s='I', fontsize=15, ha='left', c='red')
        plt.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    sequ = list('GGCUGCUUGUCCUUUAAUGGUCCAGUC')
    overall = [(key,val*100) for key,val in
               {'a': 0.7692307692307693, 'c': 0.9230769230769231, 'w': 0.7692307692307693, 'y': 0.9230769230769231, 'allForward': 0.9615384615384616, 'allBackward': 0.9230769230769231, 'all': 0.9259259259259259}.items()]
    gui = SequCovWidget( overall,
                         sequ, processCoverageData(sequ, {'a': np.array([0., 1., 0., 1., 1., 1., 0., 1., 1., 1., 0., 0., 1., 0., 1., 1., 1.,
       1., 1., 1., 1., 1., 1., 1., 1., 1., np.nan]), 'c': np.array([0., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
       1., 1., 1., 1., 1., 0., 1., 1., 1.,np.nan]), 'w': np.array([np.nan,1., 1., 0., 0., 1., 1., 0., 1., 1., 0., 1., 1., 1., 1., 1., 1., 1.,
       0., 1., 1., 1., 1., 1., 1., 1., 0.]), 'y': np.array([np.nan,1., 1., 1., 1., 1., 1., 1., 1., 1., 0., 1., 1., 1., 1., 1., 1., 1.,
       1., 1., 1., 1., 1., 1., 1., 1., 0.])}),
                         processCoverageData(sequ, {
                             'forward': np.array([0., 1., 0., 1., 1., 1., 0., 1., 1., 1., 0., 0., 1., 0., 1., 1., 1.,
                                            1., 1., 1., 1., 1., 1., 1., 1., 1., np.nan]),
                             'backward': np.array([np.nan,1., 1., 1., 1., 1., 1., 1., 1., 1., 0., 1., 1., 1., 1., 1., 1., 1.,
                                            1., 1., 1., 1., 1., 1., 1., 1., 0.])}))
    sys.exit(app.exec_())