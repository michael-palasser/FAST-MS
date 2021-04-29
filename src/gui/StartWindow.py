'''
Created on 20 Oct 2020

@author: michael
'''

from PyQt5.QtWidgets import QApplication, QPushButton, QAction

from src.gui.IsotopePatternView import IsotopePatternView
from src.gui.EditorController import *
from src.gui.ParameterDialogs import TD_configurationDialog
from src.gui.StartDialogs import IntactStartDialog
from src.top_down.ModellingTool import main as modellingTool
from src.top_down.OccupancyRecalculator import run as occupancyRecalculator
from src.top_down.SpectrumComparator import run as spectrumComparator
from src.intact.Main import run as IntactIonsSearch
from src.gui.TD_searchController import TD_MainController


class Window(AbstractMainWindow):
    def __init__(self):
        super(Window, self).__init__(None, 'SAUSAGE')
        #self.setWindowTitle('SAUSAGE')
        #self.menubar = QtWidgets.QMenuBar(self)
        #self.setMenuBar(self.menubar)
        #self.menubar.setGeometry(QtCore.QRect(0, 0, 340, 22))
        self.createMenuBar()
        self.createMenu('Top-Down Tools',
                        {'Analyse Spectrum':
                             (lambda:TD_MainController(self, True), 'Starts analysis of top-down spectrum', None),
                         'Load Analysis':
                             (lambda:TD_MainController(self, False), 'Loads an old analysis', None),
                         'Calc. Abundances':
                             (lambda: modellingTool(self), 'Calculates relative abundances of an ion list', None),
                         'Calculate Occupancies':
                             (lambda: occupancyRecalculator(self), 'Calculates occupancies of a given ion list', None),
                         'Compare Analysis':
                             (lambda: spectrumComparator(self), 'Compares the ion lists of multiple spectra', None)},
                        None)
        self.createMenu('Top-Down Configurations',
                        {'Edit Parameters':(self.editTopDownConfig, 'Edit configurations', None),
                         'Edit Fragments':(lambda: self.editData(FragmentEditorController), 'Edit fragment patterns', None),
                         'Edit Modifications':
                             (lambda: self.editData(ModificationEditorController), 'Edit modification/ligand patterns',
                              None)}, None)
        self.createMenu('Other Tools', {'Analyse Intact Ions': (lambda: self.editData(IntactIonsSearch),
                                                 'Starts analysis of spectrum with unfragmented ions', None),
                         'Edit Intact Ions': (lambda: self.editData(IntactIonsSearch), 'Edit Intact Ions', None),
                         'Isotope Pattern Tool':
                             (lambda: IsotopePatternView(self), 'Calculates the isotope pattern of an ion', None)},None)
        self.createMenu('Edit data',
                        {'Elements': (lambda: self.editData(ElementEditorController), 'Edit element table', None),
                         'Molecules': (lambda: self.editData(MoleculeEditorController), 'Edit Molecular Properties', None),
                         'Sequences': (lambda: self.editData(SequenceEditorController), 'Edit stored sequences', None)},
                        None)
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
        xPos = self.createButton('Analyse top-down\nspectrum','Starts analysis of top-down spectrum',40,
                              lambda:TD_MainController(self, True))
        xPos = self.createButton('Analyse spectrum\nof intact molecule', 'Starts analysis of normal intact spectrum',
                             xPos, self.startIntactIonSearch)
        self.setGeometry(50, 50, xPos+40, 230)
        self.show()

    def createButton(self, name, toolTip, xPos, fun):
        width = 200
        btn = QPushButton(name, self)
        btn.setToolTip(toolTip)
        btn.clicked.connect(fun)
        btn.setGeometry(QtCore.QRect(xPos, 40, width, 150))
        return xPos+width+40

    """def startFragmentHunter(self):
        dialog = TDStartDialog(self)
        dialog.show()
        if dialog.exec_() and dialog.ok:
            TD_MainController(self).start()"""

    def startIntactIonSearch(self):
        dialog = IntactStartDialog(self)
        if dialog.exec_() and dialog.ok:
            IntactIonsSearch()

    def close_application(self):
        print('exit')
        sys.exit()

    def editTopDownConfig(self):
        dialog = TD_configurationDialog(self)
        dialog.exec_()

    def editData(self, controller):
        try:
            controller()
        except CanceledException:
            pass
        '''except InvalidInputException:
            traceback.print_exc()
            print('hey')
            QtWidgets.QMessageBox.warning(self, "Problem occured", traceback.format_exc(), QtWidgets.QMessageBox.Ok)'''

def run():
    app = QApplication(sys.argv)
    gui = Window()
    sys.exit(app.exec_())


if __name__ == '__main__':
    run()