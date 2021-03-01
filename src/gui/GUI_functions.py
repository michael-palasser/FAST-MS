
from PyQt5 import QtWidgets, QtCore

translate = QtCore.QCoreApplication.translate

def makeLabelInputWidget(parent,labelName,widget):
    horizontalWidget = QtWidgets.QWidget(parent)
    horizLayout = QtWidgets.QHBoxLayout(horizontalWidget)
    label = QtWidgets.QLabel(horizontalWidget)
    label.setText(translate(parent.objectName(), labelName))
    horizLayout.addWidget(label)
    horizLayout.addWidget(widget)
    return horizLayout

def createComboBox(parent, options):
    comboBox = QtWidgets.QComboBox(parent)
    for i, option in enumerate(options):
        comboBox.addItem("")
        comboBox.setItemText(i, translate(parent.objectName(), option))
    return comboBox