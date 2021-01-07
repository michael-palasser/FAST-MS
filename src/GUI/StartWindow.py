'''
Created on 20 Oct 2020

@author: michael
'''
import sys

from PyQt5 import QtCore
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QPushButton, QAction

from src.GUI.FragmentsAndModifs import IntactIonEditorController
from src.GUI.ParameterDialogs import TDStartDialog, TD_configurationDialog, ESI_StartDialog
from src.FragmentHunter.ModellingTool import main as modellingTool
from src.FragmentHunter.OccupancyRecalculator import run as occupancyRecalculator
from src.FragmentHunter.SpectrumComparator import run as spectrumComparator
from src.Intact_Ion_Search.ESI_Main import run as IntactIonsSearch


class Window(QMainWindow):
    def __init__(self):
        super(Window, self).__init__()
        self.setWindowTitle('SAUSAGE')
        mainMenu = self.menuBar()
        self.tdMenu = mainMenu.addMenu('&FragmentHunter')
        self.esiMenu = mainMenu.addMenu('&IntactIonSearch')
        self.parameters = mainMenu.addMenu('&Storage')
        self.move(200,200)
        # self.setWindowIcon(QIcon('pic.png'))
        self.home()


    def addActionToStatusBar(self,menu, name, toolTip, function):
        action = QAction('&'+name, self)
        action.setToolTip(toolTip)
        action.triggered.connect(function)
        menu.addAction(action)


    def home(self):
        self.addActionToStatusBar(self.tdMenu, 'Analyse spectrum',
                                  'Starts analysis of top-down spectrum', self.startFragmentHunter)
        self.addActionToStatusBar(self.tdMenu, 'Remodelling',
                                  'Models relative abundance of an isotope distribution', modellingTool)
        self.addActionToStatusBar(self.tdMenu, 'Calculate occupancies',
                                  'Calculates occupancies of a given ion list', occupancyRecalculator)
        self.addActionToStatusBar(self.tdMenu, 'Compare spectra',
                                  'Compares the ion lists of multiple spectra', spectrumComparator)
        self.addActionToStatusBar(self.tdMenu, 'Edit parameters',
                                  'Edit configurations',self.editTopDownConfig)
        self.addActionToStatusBar(self.esiMenu, 'Analyse spectrum',
                                  'Starts analysis of intact spectrum', IntactIonsSearch)
        self.addActionToStatusBar(self.esiMenu, 'Edit Ions',
                                  'Edit Intact Ions', IntactIonEditorController)
        self.addActionToStatusBar(self.parameters, 'Sequences','Edit stored sequences', self.editSequences)
        xPos = self.createButton('Analyse top-down\nspectrum','Starts analysis of top-down spectrum',40,
                                  self.startFragmentHunter)
        xPos = self.createButton('Analyse spectrum\nof intact molecule', 'Starts analysis of normal ESI spectrum', xPos,
                          self.startIntactIonSearch)
        self.setGeometry(50, 50, xPos+40, 230)
        self.show()

    def createButton(self, name, toolTip, xPos, fun):
        width = 200
        btn = QPushButton(name, self)
        btn.setToolTip(toolTip)
        btn.clicked.connect(fun)
        btn.setGeometry(QtCore.QRect(xPos, 40, width, 150))
        return xPos+width+40

    def startFragmentHunter(self):
        dialog = TDStartDialog(self)
        dialog.exec_()

    def startIntactIonSearch(self):
        dialog = ESI_StartDialog(self)
        dialog.exec_()

    def close_application(self):
        print('exit')
        sys.exit()

    def editTopDownConfig(self):
        dialog = TD_configurationDialog(self)
        dialog.exec_()

    """    def editIntactIons(self):
        IntactIonEditorController()"""

    def editSequences(self):
        print('notImplemented')

def run():
    app = QApplication(sys.argv)
    gui = Window()
    sys.exit(app.exec_())


if __name__ == '__main__':
    run()