'''
Created on 20 Oct 2020

@author: michael
'''
import sys

from PyQt5 import QtCore
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QPushButton, QAction

from src.views.EditorController import *
from src.views.ParameterDialogs import TDStartDialog, TD_configurationDialog, IntactStartDialog
from src.top_down.ModellingTool import main as modellingTool
from src.top_down.OccupancyRecalculator import run as occupancyRecalculator
from src.top_down.SpectrumComparator import run as spectrumComparator
from src.intact.Main import run as IntactIonsSearch


class Window(QMainWindow):
    def __init__(self):
        super(Window, self).__init__()
        self.setWindowTitle('SAUSAGE')
        mainMenu = self.menuBar()
        self.tdMenu = mainMenu.addMenu('&Top-Down Tools')
        self.tdEditMenu = mainMenu.addMenu('&Top-Down Configurations')
        self.esiMenu = mainMenu.addMenu('&IntactIonSearch')
        self.dataEdit = mainMenu.addMenu('&Edit data')
        self.move(200,200)
        # self.setWindowIcon(QIcon('pic.png'))
        self.home()


    def addActionToStatusBar(self,menu, name, toolTip, function):
        action = QAction('&'+name, self)
        action.setToolTip(toolTip)
        action.setWhatsThis(toolTip)
        action.setStatusTip(toolTip)
        action.triggered.connect(function)
        menu.addAction(action)


    def home(self):
        self.addActionToStatusBar(self.tdMenu, 'Analyse Spectrum',
                                  'Starts analysis of top-down spectrum', self.startFragmentHunter)
        self.addActionToStatusBar(self.tdMenu, 'FragmentIon Modelling',
                                  'Models relative abundance of an isotope distribution', modellingTool)
        self.addActionToStatusBar(self.tdMenu, 'Calculate Occupancies',
                                  'Calculates occupancies of a given ion list', occupancyRecalculator)
        self.addActionToStatusBar(self.tdMenu, 'Compare Analysis',
                                  'Compares the ion lists of multiple spectra', spectrumComparator)
        self.addActionToStatusBar(self.tdEditMenu, 'Edit Parameters',
                                  'Edit configurations',self.editTopDownConfig)
        self.addActionToStatusBar(self.tdEditMenu, 'Edit Fragments',
                                  'Edit fragment patterns',FragmentEditorController)
        self.addActionToStatusBar(self.tdEditMenu, 'Edit Modifications',
                                  'Edit modification/ligand patterns',ModificationEditorController)
        self.addActionToStatusBar(self.esiMenu, 'Analyse spectrum',
                                  'Starts analysis of intact spectrum', IntactIonsSearch)
        self.addActionToStatusBar(self.esiMenu, 'Edit Ions',
                                  'Edit Intact Ions', IntactIonEditorController)
        self.addActionToStatusBar(self.dataEdit, 'Elements','Edit element table ', ElementEditorController)
        self.addActionToStatusBar(self.dataEdit, 'Molecules','Edit Molecular Properties', MoleculeEditorController)
        self.addActionToStatusBar(self.dataEdit, 'Sequences','Edit stored sequences', SequenceEditorController)
        xPos = self.createButton('Analyse top-down\nspectrum','Starts analysis of top-down spectrum',40,
                                  self.startFragmentHunter)
        xPos = self.createButton('Analyse spectrum\nof intact molecule', 'Starts analysis of normal intact spectrum', xPos,
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
        dialog = IntactStartDialog(self)
        dialog.exec_()

    def close_application(self):
        print('exit')
        sys.exit()

    def editTopDownConfig(self):
        dialog = TD_configurationDialog(self)
        dialog.exec_()


def run():
    app = QApplication(sys.argv)
    gui = Window()
    sys.exit(app.exec_())


if __name__ == '__main__':
    run()