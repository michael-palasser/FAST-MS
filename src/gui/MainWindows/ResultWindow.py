'''
Created on 21 Jul 2020

@author: michael
'''
import os
from PyQt5 import QtWidgets

from src.gui.GUI_functions import translate
from src.gui.MainWindows.AbstractMainWindows import SimpleMainWindow
from src.resources import path
from src.gui.tableviews.TableViews import TableView
from src.gui.tableviews.TableModels import IonTableModel


class ResultWindow(SimpleMainWindow):

    def __init__(self, title, configs, observedIons, deletedIons, showOptions):
        '''
        Opens a SimpleMainWindow with the ion lists and a InfoView with the protocol
        '''
        super().__init__(None, title)
        self._openWindows = []
        self._translate = translate
        #self._openWindows.append(self._mainWindow)
        self._centralwidget = self.centralWidget()
        self._configs = configs
        self.verticalLayout = QtWidgets.QVBoxLayout(self._centralwidget)
        self._tabWidget = QtWidgets.QTabWidget(self._centralwidget)
        #self._infoView = InfoView(None, self._info)
        #self._openWindows.append(self._infoView)
        self.createMenuBar()
        self.makeHelpMenu()
        self.fillMainWindow(observedIons, deletedIons, showOptions)
        self.resize(1000, 900)
        self.show()

    def shootPic(self):
        widgets = {w.windowTitle():w for w in self._openWindows}
        item, ok = QtWidgets.QInputDialog.getItem(self, "Shoot",
                                        "Select the window", list(widgets.keys()), 0, False)
        if ok and item:
            p=widgets[item].grab()
            p.save(os.path.join(path,'pics',item+'.png'), 'png')
            print('Shoot taken')

    def fillMainWindow(self, observedIons, deletedIons, showOptions):
        '''
        Makes a QTabWidget with the ion tables
        :return:
        '''
        self._tables = []
        for table, name in zip((observedIons, deletedIons),('Observed Ions', 'Deleted Ions')):
            self.makeTabWidget(table, name, showOptions)
        self.verticalLayout.addWidget(self._tabWidget)

    def makeTabWidget(self, data, name, showOptions):
        '''
        Makes a tab in the tabwidget
        :param data:
        :param name:
        :return:
        '''
        tab = QtWidgets.QWidget()
        verticalLayout = QtWidgets.QVBoxLayout(tab)
        self._tabWidget.addTab(tab, "")
        self._tabWidget.setTabText(self._tabWidget.indexOf(tab), self._translate(self.objectName(), name))
        scrollArea,table = self.makeScrollArea(tab,[ion.getMoreValues() for ion in data.values()], showOptions)
        verticalLayout.addWidget(scrollArea)
        self._tables.append(table)
        self._tabWidget.setEnabled(True)

    def makeScrollArea(self, parent, data, fun):
        '''
        Makes QScrollArea for ion tables
        '''
        scrollArea = QtWidgets.QScrollArea(parent)
        scrollArea.setWidgetResizable(True)
        table = self.makeTable(scrollArea, data, fun)
        table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        table.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        scrollArea.setWidget(table)
        return scrollArea, table

    def makeTable(self, parent, data,fun, precursorRegion=None):
        '''
        Makes an ion table
        '''
        tableModel = IonTableModel(data, precursorRegion, self._configs['shapeMarked'], self._configs['scoreMarked'])
        table = TableView(parent, tableModel, fun, 3)
        return table


