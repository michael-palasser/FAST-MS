import os
from functools import partial
import pandas as pd

from PyQt5 import QtWidgets, QtCore

from src import path

translate = QtCore.QCoreApplication.translate

def makeLabelInputWidget(parent,labelName,*args):
    horizontalWidget = QtWidgets.QWidget(parent)
    horizLayout = QtWidgets.QHBoxLayout(horizontalWidget)
    label = QtWidgets.QLabel(horizontalWidget)
    label.setText(translate(parent.objectName(), labelName))
    horizLayout.addWidget(label)
    for widget in args:
        horizLayout.addWidget(widget)
    return horizontalWidget, horizLayout

def createComboBox(parent, options, comboBox=None):
    if comboBox is None:
        comboBox = QtWidgets.QComboBox(parent)
    for i, option in enumerate(options):
        comboBox.addItem("")
        comboBox.setItemText(i, translate(parent.objectName(), option))
    return comboBox

def makeFormLayout(parent):
    formLayout = QtWidgets.QFormLayout(parent)
    formLayout.setHorizontalSpacing(12)
    formLayout.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)
    formLayout.setLabelAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
    formLayout.setFormAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
    return formLayout


def connectTable(table, fun):
    table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
    table.customContextMenuRequested['QPoint'].connect(partial(fun, table))

'''def showOptions(table, pos):
    menu = QtWidgets.QMenu()
    copyAction = menu.addAction("Copy Table")
    action = menu.exec_(table.viewport().mapToGlobal(pos))
    if action == copyAction:
        df=pd.DataFrame(data=table.model().getData(), columns=table.model().getHeaders())
        df.to_clipboard(index=False,header=True)'''

def showOptions(table, pos):
    menu = QtWidgets.QMenu()
    copyAllAction = menu.addAction("Copy Table")
    copyAction = menu.addAction("Copy Cell")
    action = menu.exec_(table.viewport().mapToGlobal(pos))
    data, headers = getData(table)
    if action == copyAction:
        it = table.indexAt(pos)
        if it is None:
            return
        selectedRow = it.row()
        selectedCol = it.column()
        #df = pd.DataFrame(data=[table.model().getData()[selectedRow][selectedCol]])
        df = pd.DataFrame(data=[data[selectedRow][selectedCol]])
        df.to_clipboard(index=False, header=False)
    elif action == copyAllAction:
        df = pd.DataFrame(data=data, columns=headers)
        df.to_clipboard(index=False, header=True)

def getData(table):
    if isinstance(table, QtWidgets.QTableWidget):
        return table.getData(), table.getHeaders()
    else:
        return [list(row) for row in table.model().getData()], table.model().getHeaders()



def shoot(widget):
    #filename = datetime.now().strftime('%Y-%m-%d_%H-%M-%S.png')
    p=widget.grab()
    p.save(os.path.join(path,'pics',widget.windowTitle()+'.png'), 'png')
    print('Shot taken')