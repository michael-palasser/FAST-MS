# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'TDStartWidget.ui'
#
# Created by: PyQt5 UI code generator 5.15.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_startDialog(object):
    def setupUi(self, startDialog):
        startDialog.setObjectName("startDialog")
        startDialog.resize(412, 307)
        self.buttonBox = QtWidgets.QDialogButtonBox(startDialog)
        self.buttonBox.setGeometry(QtCore.QRect(210, 260, 164, 32))
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.layoutWidget = QtWidgets.QWidget(startDialog)
        self.layoutWidget.setGeometry(QtCore.QRect(30, 20, 351, 216))
        self.layoutWidget.setObjectName("layoutWidget")
        self.gridLayout = QtWidgets.QGridLayout(self.layoutWidget)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")
        self.noiseLimit = QtWidgets.QDoubleSpinBox(self.layoutWidget)
        self.noiseLimit.setObjectName("noiseLimit")
        self.gridLayout.addWidget(self.noiseLimit, 4, 1, 1, 1)
        self.labelSequ = QtWidgets.QLabel(self.layoutWidget)
        self.labelSequ.setObjectName("labelSequ")
        self.gridLayout.addWidget(self.labelSequ, 0, 0, 1, 1)
        self.sequence = QtWidgets.QLineEdit(self.layoutWidget)
        self.sequence.setObjectName("sequenceList")
        self.gridLayout.addWidget(self.sequence, 0, 1, 1, 1)
        self.labelCharge = QtWidgets.QLabel(self.layoutWidget)
        self.labelCharge.setObjectName("labelCharge")
        self.gridLayout.addWidget(self.labelCharge, 1, 0, 1, 1)
        self.charge = QtWidgets.QSpinBox(self.layoutWidget)
        self.charge.setObjectName("charge")
        self.gridLayout.addWidget(self.charge, 1, 1, 1, 1)
        self.labelMod = QtWidgets.QLabel(self.layoutWidget)
        self.labelMod.setObjectName("labelModif")
        self.gridLayout.addWidget(self.labelMod, 2, 0, 1, 1)
        self.modification = QtWidgets.QLineEdit(self.layoutWidget)
        self.modification.setObjectName("modification")
        self.gridLayout.addWidget(self.modification, 2, 1, 1, 1)
        self.labelNoise = QtWidgets.QLabel(self.layoutWidget)
        self.labelNoise.setObjectName("labelNoise")
        self.gridLayout.addWidget(self.labelNoise, 4, 0, 1, 1)
        self.labelMode = QtWidgets.QLabel(self.layoutWidget)
        self.labelMode.setObjectName("labelMode")
        self.gridLayout.addWidget(self.labelMode, 5, 0, 1, 1)
        self.sprayMode = QtWidgets.QComboBox(self.layoutWidget)
        self.sprayMode.setObjectName("sprayMode")
        self.sprayMode.addItem("")
        self.sprayMode.addItem("")
        self.gridLayout.addWidget(self.sprayMode, 5, 1, 1, 1)
        self.labelDiss = QtWidgets.QLabel(self.layoutWidget)
        self.labelDiss.setObjectName("labelDiss")
        self.gridLayout.addWidget(self.labelDiss, 6, 0, 1, 1)
        self.dissociation = QtWidgets.QComboBox(self.layoutWidget)
        self.dissociation.setObjectName("dissociation")
        self.dissociation.addItem("")
        self.dissociation.addItem("")
        self.dissociation.addItem("")
        self.gridLayout.addWidget(self.dissociation, 6, 1, 1, 1)
        self.labelData = QtWidgets.QLabel(self.layoutWidget)
        self.labelData.setObjectName("labelData")
        self.gridLayout.addWidget(self.labelData, 3, 0, 1, 1)
        self.spectralData = QtWidgets.QLineEdit(self.layoutWidget)
        self.spectralData.setObjectName("spectralData")
        self.gridLayout.addWidget(self.spectralData, 3, 1, 1, 1)
        self.defaultButton = QtWidgets.QPushButton(startDialog)
        self.defaultButton.setGeometry(QtCore.QRect(40, 260, 113, 32))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.defaultButton.sizePolicy().hasHeightForWidth())
        self.defaultButton.setSizePolicy(sizePolicy)
        self.defaultButton.setMinimumSize(QtCore.QSize(113, 0))
        self.defaultButton.setObjectName("defaultButton")

        self.retranslateUi(startDialog)
        QtCore.QMetaObject.connectSlotsByName(startDialog)

    def retranslateUi(self, startDialog):
        _translate = QtCore.QCoreApplication.translate
        startDialog.setWindowTitle(_translate("startDialog", "Dialog"))
        self.labelSequ.setText(_translate("startDialog", "sequenceList name"))
        self.labelCharge.setText(_translate("startDialog", "charge"))
        self.charge.setWhatsThis(_translate("startDialog", "<html><head/><body><p>charge state of precursor ion</p></body></html>"))
        self.labelMod.setText(_translate("startDialog", "modification"))
        self.labelNoise.setText(_translate("startDialog", "noise threshold (x10^6)"))
        self.labelMode.setText(_translate("startDialog", "spray mode"))
        self.sprayMode.setCurrentText(_translate("startDialog", "positive"))
        self.sprayMode.setItemText(0, _translate("startDialog", "positive"))
        self.sprayMode.setItemText(1, _translate("startDialog", "negative"))
        self.labelDiss.setText(_translate("startDialog", "dissociation"))
        self.dissociation.setItemText(0, _translate("startDialog", "CAD"))
        self.dissociation.setItemText(1, _translate("startDialog", "ECD"))
        self.dissociation.setItemText(2, _translate("startDialog", "EDD"))
        self.labelData.setText(_translate("startDialog", "spectral pattern"))
        self.defaultButton.setText(_translate("startDialog", "last used"))