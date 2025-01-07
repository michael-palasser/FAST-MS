import os
import sys
from functools import partial
import pandas as pd

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QIcon

from src.resources import path, DEVELOP

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

def createComboBox(parent, options, comboBox=None, tooltips=None):
    if comboBox is None:
        comboBox = QtWidgets.QComboBox(parent)
    for i, option in enumerate(options):
        comboBox.addItem("")
        comboBox.setItemText(i, translate(parent.objectName(), option))
        if tooltips is not None:
            comboBox.setItemData(i, tooltips[i], QtCore.Qt.ToolTipRole)
    return comboBox

def makeToolBox(parent, options):
    button = QtWidgets.QToolButton(parent)
    menu = QtWidgets.QMenu()
    for key, vals in options.items():
        #sub_menu = menu.addMenu(key)
        sub_menu = QtWidgets.QMenu(key, menu)
        for i, option in enumerate(vals):
            print(option)
            action = sub_menu.addAction(option)
            #action.triggered.connect(lambda: button.setText('{0}_{1}'.format(key, option)))
    button.setMenu(menu)
    """button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
    button.setStyleSheet('QToolButton::menu-indicator { image: none; }')"""
    return button


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
    if DEVELOP:
        #filename = datetime.now().strftime('%Y-%m-%d_%H-%M-%S.png')
        p=widget.grab()
        p.save(os.path.join(path,'pics',widget.windowTitle()+'.png'), 'png')
        print('Shot taken')

def setIcon(widget):
    widget.setWindowIcon(QIcon(getIconPath('icon.ico')))

def getIconPath(fileName):
    return os.path.join(getattr(sys, '_MEIPASS', path), fileName)

def makeButton(parent, name, toolTip, fun):
    btn = QtWidgets.QPushButton(name, parent)
    btn.setToolTip(toolTip)
    btn.clicked.connect(fun)
    return btn


def fillFormLayout(parent, labelNames, widgets, *args):
    '''
    Fills a QFormLayout with labels and corresponding widgets
    :param parent:
    :param (list[str] | tuple[str]) labelNames:
    :param (dict[str, tuple[QWidget, str]]) widgets: dict of name (widget, tooltip)
    :param args: tuple of minimum and maximum width
    :return:
    '''
    formLayout = makeFormLayout(parent)
    index = 0
    for labelName, key in zip(labelNames, widgets.keys()):
        tup = widgets[key]
        makeLine(parent, formLayout, index, labelName, tup, args)
        widgets[key] = tup[0]
        index += 1
    return formLayout

def makeLine(parent, formLayout, yPos, labelName, widgetTuple, *args):
    '''
    Sets a label and the corresponding widget into a QFormlayout
    :param parent:
    :param (QFormLayout) formLayout:
    :param (int) yPos: row index
    :param (str) labelName:
    :param (str) widgetKey:
    :param (tuple[QWidget, str]) widgetTuple: (widget, tooltip)
    :param (tuple(tuple[int,int])) args: tuple of minimum and maximum width
    '''
    widgetSizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
    label = QtWidgets.QLabel(parent)
    label.setText(translate(label.objectName(), labelName))
    widget = widgetTuple[0]
    if args and args[0]:
        label.setMinimumWidth(args[0][0])
        widget.setMaximumWidth(args[0][1])
    formLayout.setWidget(yPos, QtWidgets.QFormLayout.LabelRole, label)
    widget.setParent(parent)
    #widget.setObjectName(widgetName)
    widget.setToolTip(translate(widget.objectName(), widgetTuple[1]))
    widgetSizePolicy.setHeightForWidth(widget.sizePolicy().hasHeightForWidth())
    widget.setSizePolicy(widgetSizePolicy)
    formLayout.setWidget(yPos, QtWidgets.QFormLayout.FieldRole, widget)


def makeScrollArea(parent, table):
    '''
    Makes QScrollArea for ion tables
    '''
    scrollArea = QtWidgets.QScrollArea(parent)
    scrollArea.setWidgetResizable(True)
    table.setParent(scrollArea)
    table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
    table.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
    scrollArea.setWidget(table)
    return scrollArea

def makeSpinBox(parent, decimals=None, val=0, minMax=None):
    if decimals is None:
        w = QtWidgets.QSpinBox(parent)
    else:
        w = QtWidgets.QDoubleSpinBox(parent)
        w.setDecimals(decimals)
    w.setMinimum(minMax[0])
    w.setMaximum(minMax[1])
    w.setValue(val)
    return w

