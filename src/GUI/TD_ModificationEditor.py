'''
Created on 29 Dec 2020

@author: michael
'''

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QDialog, QMessageBox, QMainWindow
from src import path
from src.ConfigurationHandler import ConfigHandler
from src.FragmentHunter import Main
from src.Intact_Ion_Search import ESI_Main
from os.path import join

class TD_ModificationEditior(QMainWindow):
    def __init__(self, dialogName, title, lineSpacing, parent=None):
        super().__init__(parent)
        #self.setObjectName(dialogName)
        #self.lineSpacing = lineSpacing
        self.widgets = dict()
        #self.sizePolicy = self.setNewSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self._translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(self._translate(dialogName, title))
        self.buttonBox = QtWidgets.QDialogButtonBox(self)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.move(300,100)