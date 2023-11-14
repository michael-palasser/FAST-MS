import traceback
from copy import deepcopy

import numpy as np
import matplotlib
from matplotlib import pyplot as plt
import matplotlib.ticker as mticker

#import matplotlib.path as mpath

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import Qt, QVariant
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

from src.gui.GUI_functions import makeLabelInputWidget, createComboBox, setIcon, translate
from src.gui.tableviews.TableModels import AbstractTableModel
from src.gui.tableviews.TableViews import TableView


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
            #if (row!=0) and (row!=len(self._data)-1) and (col!=0):
            #if (row != len(self._data) - 1) and (col != 0):
            if self._data[row][col]==1:
                return QVariant(QtGui.QColor(Qt.darkGreen))
            elif self._data[row][col]==0:
                return QVariant(QtGui.QColor(Qt.lightGray))

    def sort(self, Ncol, order):
        """
        Sort table by selected column
        """
        self.layoutAboutToBeChanged.emit()
        #self._data = self._data.sort_values(self._headers[Ncol], ascending=order == Qt.AscendingOrder)
        if order == Qt.AscendingOrder:
            #self._data.sort(key= lambda tup:tup[Ncol])
            #data = sorted(self._data[1:-1], key= lambda tup:tup[Ncol])
            data = sorted(self._data[:-1], key= lambda tup:tup[Ncol])
        else:
            #self._data.sort(key= lambda tup:tup[Ncol], reverse=True)
            #data = sorted(self._data[1:-1],key= lambda tup:tup[Ncol], reverse=True)
            data = sorted(self._data[:-1],key= lambda tup:tup[Ncol], reverse=True)
        #self._data = [self._data[0]]+data+[self._data[-1]]
        self._data = data + [self._data[-1]]
        self.layoutChanged.emit()


class SequCovTableModel(AbstractTableModel):
    '''
    TableModel for a QTableView in SequCovWidget which shows the sequence coverage for each fragment type
    '''
    def __init__(self, data):
        super(SequCovTableModel, self).__init__(data, (), ('type', 'coverage /%'))

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
        self._translate = translate
        self._coveragesForw = coveragesForw
        self._coveragesBackw = coveragesBackw
        self._globalData = globalData
        self._noCleavageSites = len(sequence) - 1
        verticalLayout = QtWidgets.QVBoxLayout(self)
        """model = SequCovTableModel(values)
        table = QtWidgets.QTableView(self)
        table.setModel(model)
        table.setSortingEnabled(True)
        connectTable(table,showOptions)"""
        table = TableView(self, SequCovTableModel(values))
        table.sortByColumn(0, Qt.AscendingOrder)
        #table.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        table.resizeColumnsToContents()
        [table.setRowHeight(i,23) for i in range(len(values))]
        table.setMinimumHeight((len(values)+1)*23)
        verticalLayout.addWidget(table)
        all = deepcopy(coveragesForw)
        all.update(coveragesBackw)
        coverageData = self.addCleavageSites([[key] + list(val) for key,val in all.items()])
        verticalLayout.addWidget(self.makeCoverageTable(coverageData, ['fragm.'] + [i+1 for i in range(len(sequence)-1)]))
        #verticalLayout.addWidget(self.makeCoverageTable(coverageData, ['Fragm.'] + [str(i+1) for i in range(self._sequLength)]))
        #verticalLayout.addWidget(self.makeCoverageTable(globalData, ['direction'] + sequence))
        width = 10
        if self._noCleavageSites>=200:
            width = 30
        elif self._noCleavageSites>=100:
            width = 20
        elif self._noCleavageSites>=50:
            width = 15
        self._lineWidth = QtWidgets.QSpinBox()
        self._lineWidth.setValue(width)
        self._lineWidth.setMaximum(999)
        updateBtn = QtWidgets.QPushButton()
        updateBtn.setText('Update')
        widg, _ = makeLabelInputWidget(self, 'res. per line:', self._lineWidth, updateBtn)
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
        self._sequPlot = SequenceCoveragePlot(sequence, globalData[:,0].reshape((self._noCleavageSites, 1)),
                                              globalData[:,1].reshape((self._noCleavageSites, 1)), width)
        updateBtn.clicked.connect(self.updatePlot)
        setIcon(self)

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
        """model = SequCovPlotTableModel(data, headers)
        table = QtWidgets.QTableView(self)
        # self._table.setSortingEnabled(True)
        table.setModel(model)
        connectTable(table,showOptions)"""
        #table.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        table = TableView(self, SequCovPlotTableModel(data, headers))
        table.sortByColumn(0, Qt.AscendingOrder)
        table.setSortingEnabled(False)
        table.resizeColumnsToContents()
        table.setColumnWidth(0,70)
        table.resizeRowsToContents()
        #table.resize(70+len(data[0])*table.columnWidth(1), (len(data)+1)*table.rowHeight(0))
        return table


    def addCleavageSites(self, data):
        newData = data #[[''] + [str(i + 1) for i in range(self._sequLength)]]+data
        newData.append([''] + [str(self._noCleavageSites - i) for i in range(self._noCleavageSites)])
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
            if tup[0].isChecked():
                if key in self._coveragesForw.keys():
                        forward.append(self._coveragesForw[key])
                        forwardC.append(tup[1].currentText())
                elif key in self._coveragesBackw.keys():
                        backward.append(self._coveragesBackw[key])
                        backwardC.append(tup[1].currentText())
        forward2,backward2 = [],[]
        for i in range(self._noCleavageSites):
            forward2.append([arr[i] for arr in forward])
            backward2.append([arr[i] for arr in backward])
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
        sequLength=len(self._sequence)
        rows = int(sequLength / lineWidth)+1
        step_x = 1
        step_y = 1/(2*rows)
        #print('rows', rows, sequLength,step_y)
        self._fig = plt.figure(figsize=(lineWidth,rows+0))
        matplotlib.rcParams.update({'font.size': 15})
        ax = plt.subplot(111)
        ax.set_xlim([-step_x*0.5, lineWidth+0.5])
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
        nrSize= 10
        plt.text(x=-step_x*0.6, y=1-line, s=str(counter), fontsize=nrSize)
        #size = 0.01
        for i,bb in enumerate(self._sequence):
            plt.text(x=xPos, y=1-line, s=bb, fontsize=20, ha='center')
            if i != sequLength-1:
                for j,coverageForward in enumerate(coveragesForward[i]):
                    if coverageForward and not np.isnan(coverageForward):
                        yPos_j=1-line+step_y*0.6+(len(coveragesForward[i])-j-1)*step_y*0.2
                        plt.text(x=xPos+step_x*0.491, y=yPos_j, s='L', ha='center', c=coloursF[j],rotation=180)
                        plt.text(x=xPos+step_x*0.586, y=1-line+step_y*0.15, s='I', ha='center', c=coloursF[-1])
                '''if (i+1)%lineWidth:
                    xPos+=step_x'''
                '''if not (i + 1) % lineWidth:
                    line += 2 * step_y
                    plt.text(x=-step_x * 0.5, y=1 - line, s=str(counter), fontsize=nrSize)
                    xPos = step_x / 2'''
            if i != 0:
                for j,coverageBackward in enumerate(coveragesBackward[i-1]):
                    if coverageBackward and not np.isnan(coverageBackward):
                        yPos_j=1-line-step_y*0.3-(len(coveragesBackward[i-1])-j-1)*step_y*0.2
                        #plt.text(x=xPos+step_x*0.62, y=yPos_j, s='L', ha='left', c=coloursB[j])
                        plt.text(x=xPos-step_x*0.375, y=yPos_j, s='L', ha='center', c=coloursB[j])
                        plt.text(x=xPos-step_x*0.414, y=1-line-step_y*0.15, s='I', ha='center', c=coloursB[-1])
                        #if (not coveragesForward[i]) or (xPos==step_x/2):
                        #plt.text(x=xPos+step_x*0.62, y=1-line-step_y*0.05, s='I', ha='left', c=coloursB[-1])

            counter += 1
        #plt.savefig('foo.png')
            if (i+1)%lineWidth:
                xPos+=step_x
            else:
                line += 2 * step_y
                plt.text(x=-step_x * 0.5, y=1 - line, s=str(counter), fontsize=nrSize)
                xPos = step_x / 2

        plt.show()


"""if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys
    
    sequ = list('GGCUGCUUGUCCUUUAAUGGUCCAGUC')
    app = QApplication(sys.argv)
    overall = [(key,val*100) for key,val in
               {'a': 0.7692307692307693, 'c': 0.9230769230769231, 'w': 0.7692307692307693, 'y': 0.9230769230769231, 'allForward': 0.9615384615384616, 'allBackward': 0.9230769230769231, 'all': 0.9259259259259259}.items()]
    gui = SequCovWidget( overall,
                         sequ, {'a': np.array([0., 1., 0., 1., 1., 1., 0., 1., 1., 1., 0., 0., 1., 0., 1., 1., 1.,
       1., 1., 1., 1., 1., 1., 1., 1., 1., np.nan]), 'c': np.array([0., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1.,
       1., 1., 1., 1., 1., 0., 1., 1., 1.,np.nan])}, {'w': np.array([np.nan,1., 1., 0., 0., 1., 1., 0., 1., 1., 0., 1., 1., 1., 1., 1., 1., 1.,
       0., 1., 1., 1., 1., 1., 1., 1., 0.]), 'y': np.array([np.nan,1., 1., 1., 1., 1., 1., 1., 1., 1., 0., 1., 1., 1., 1., 1., 1., 1.,
       1., 1., 1., 1., 1., 1., 1., 1., 0.])},np.array([(val1,val2) for val1,val2 in zip(np.array([0., 1., 0., 1., 1., 1., 0., 1., 1., 1., 0., 0., 1., 0., 1., 1., 1.,
                                            1., 1., 1., 1., 1., 1., 1., 1., 1., np.nan]),np.array([np.nan,1., 1., 1., 1., 1., 1., 1., 1., 1., 0., 1., 1., 1., 1., 1., 1., 1.,
                                            1., 1., 1., 1., 1., 1., 1., 1., 0.]))]))'''

    '''sequ = list('GGCUGCUUGUCCUUUAAUGGUCCAGUC')*10
    sequLength = len(sequ)
    sequPlot = SequenceCoveragePlot(sequ, np.ones((sequLength,1)),
                                          np.ones((sequLength,1)), 20)'''

    star = matplotlib.markers.TICKLEFT
    print(star)
    circle = mpath.Path.unit_circle()
    # concatenate the circle with an internal cutout of the star
    '''verts = np.concatenate([circle.vertices, star])
    codes = np.concatenate([circle.codes, star])
    cut_star = mpath.Path(verts, codes)
    plt.plot(np.arange(10) ** 2, '--r', marker=cut_star, markersize=15)

    plt.show()
    #sys.exit(app.exec_())"""