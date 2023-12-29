'''
Created on 20 Oct 2020

@author: michael
'''
import sys

from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QApplication, QPushButton

from src.gui.controller.IntactSearchController import IntactMainController
from src.gui.controller.IsotopePatternView import IsotopePatternView
from src.gui.controller.EditorController import *
from src.gui.dialogs.ParameterDialogs import ConfigurationDialog
from src.gui.dialogs.StartDialogs import IntactStartDialog
from src.top_down.OccupancyRecalculator import run as occupancyRecalculator
from src.top_down.SpectrumComparator import run as spectrumComparator
from src.intact.Main import run as IntactIonsSearch
from src.gui.controller.TD_searchController import TD_MainController
from src.resources import INTERN

if INTERN:
    from src.BACHEM_extension.gui.MainController_extension import MD_MainController
    from src.BACHEM_extension.gui.Dialogs_extension import MDStartDialog
    from src.BACHEM_extension.gui.SequenceTranslater import SequenceTranslaterWindow
    from src.BACHEM_extension.services.TD_Assigner import TD_Assigner
    from src.BACHEM_extension.gui.MainController_extension import BACHEM_MainController as TD_MainController




class Window(SimpleMainWindow):
    '''
    Main window which pops up when SAUSAGE is started
    '''
    def __init__(self):
        super(Window, self).__init__(None, 'FAST MS')
        self._layout = QtWidgets.QHBoxLayout(self._centralwidget)
        self._layout.setContentsMargins(40,25,40,40)
        self.createMenuBar()
        self.createMenu('Top-Down',
                        {'Analyse Spectrum':
                             (lambda:self.startTopDown(True), 'Starts analysis of top-down spectrum', None),
                         'Load Analysis':
                             (lambda:self.startTopDown(False), 'Loads an old analysis', None),
                         'Open Current Analysis':
                             (self.reopen, 'Re-opens the last analysis', None),
                         #'Calc. Abundances':
                         #    (lambda: modellingTool(self), 'Calculates relative abundances of an ion list', None),
                         'Calculate Occupancies':
                             (lambda: occupancyRecalculator(self), 'Calculates occupancies of a given (fragment) ion list', None),
                         'Edit Fragments': (
                         lambda: self.editData(FragmentEditorController), 'Edit fragment patterns', None),
                         'Edit Modifications':
                             (lambda: self.editData(ModificationEditorController), 'Edit modification/ligand patterns',
                              None)}, None)
        #[print(action.toolTip()) for action in menuActions.values()]
        #print(menu.toolTipsVisible())
        self.createMenu('Intact Ions',
                        {'Analyse Spectrum': (
                        lambda: self.startIntact(True), 'Starts analysis of intact ion spectrum', None),
                         'Assign Intact Ions': (lambda: self.editData(self.startIntactIonSearch),
                                                 'Starts assignment and analysis of lists with unfragmented ions', None),
                         'Edit Intact Ions': (
                         lambda: self.editData(IntactIonEditorController), 'Edit Intact Ions', None)}, None)
        self.createMenu('Other Tools',
                        {'Model Ion':
                             (self.openIonModeller, 'Calculates the isotope pattern of an ion', None),
                         'Compare Ion Lists':
                             (self.compareSpectra, 'Compares the ion lists of multiple spectra', None)},None)
        if INTERN:
            self.createMenu('4 BACHEM',
                            {#'Simple MS/MS Method Development':
                             #   (self.startSimpleMD, 'Calculates occupancies of a given (fragment) ion list', None),"""
                            'MS/MS Method Development':
                                (lambda:self.startFullMD(True), 'Starts the analysis of an MS/MS spectrum for method development', None),
                            'SequenceTranslater':
                                (self.openTranslater, 'Translates a sequence in HELM or 3-letter code to FAST MS sequence', None),
                            'Load MS/MS MD':
                                (lambda:self.startFullMD(False), 'Loads an old MS/MS method development analysis', None),},
                            None)

        self.createMenu('Edit',
                        {'Configurations':(self.editTopDownConfig, 'Edit configurations', None),
                         'Elements': (lambda: self.editData(ElementEditorController), 'Edit element table', None),
                         'Molecules': (lambda: self.editData(MoleculeEditorController), 'Edit Molecular Properties', None),
                         'Sequences': (lambda: self.editData(SequenceEditorController), 'Edit stored sequences', None)},
                        None)
        self.makeHelpMenu()
        self.move(200,200)
        # self.setWindowIcon(QIcon('pic.png'))
        self._lastSearch = None
        self.showButtons()
        self._openWindows=[]

    def showButtons(self):
        btn = self.makeButton('Analyse Top-Down\nSpectrum', 'Starts analysis of top-down spectrum',
                              lambda:self.startTopDown(True))
        self._layout.addWidget(btn)
        self._layout.setSpacing(30)
        btn = self.makeButton('Assign\nIntact Ions', 'Starts assignment and analysis of lists with unfragmented ions',
                              self.startIntactIonSearch)
        self._layout.addWidget(btn)
        #self.setGeometry(50, 50, xPos+40, 230)
        self.show()

    def startTopDown(self, new):
        self._lastSearch = SimpleMainWindow(None, '')
        TD_MainController(self, new, self._lastSearch)

    def startIntact(self, new):
        self._lastSearch = SimpleMainWindow(None, '')
        IntactMainController(self, new, self._lastSearch)

    def reopen(self):
        if self._lastSearch is not None:
            self._lastSearch.show()

    def makeButton(self, name, toolTip, fun):
        btn = QPushButton(name, self._centralwidget)
        btn.setToolTip(toolTip)
        btn.clicked.connect(fun)
        btn.setMinimumSize(QSize(200, 150))
        return btn


    def startIntactIonSearch(self):
        dialog = IntactStartDialog(self)
        if dialog.exec_() and dialog.ok:
            try:
                IntactIonsSearch()
            except InvalidInputException as e:
                traceback.print_exc()
                QtWidgets.QMessageBox.warning(self, "Problem occured", e.__str__(), QtWidgets.QMessageBox.Ok)

    def openIonModeller(self):
        self._openWindows.append(IsotopePatternView(None))

    def compareSpectra(self):
        try:
            spectrumComparator(self)
        except InvalidInputException as e:
            traceback.print_exc()
            QtWidgets.QMessageBox.warning(self, "Problem occured", e.__str__(), QtWidgets.QMessageBox.Ok)


    def close_application(self):
        print('exit')
        sys.exit()

    def editTopDownConfig(self):
        dialog = ConfigurationDialog(self)
        dialog.exec_()

    def editData(self, controller):
        try:
            self._openWindows.append(controller())
        except CanceledException:
            pass
        except InvalidInputException as e:
            traceback.print_exc()
            QtWidgets.QMessageBox.warning(self, "Problem occured", e.__str__(), QtWidgets.QMessageBox.Ok)

    def startSimpleMD(self):
        if INTERN:
            dialog = MDStartDialog(self)
            if dialog.exec_() and dialog.ok:
                try:
                    assigner = TD_Assigner()
                    assigner.search()
                except InvalidInputException as e:
                    traceback.print_exc()
                    QtWidgets.QMessageBox.warning(self, "Problem occured", e.__str__(), QtWidgets.QMessageBox.Ok)
        else:
            pass

    def startFullMD(self, new=True):
        if INTERN:
            self._lastSearch = SimpleMainWindow(None, '')
            if new:
                MD_MainController(self, True, self._lastSearch)
            else:
                MD_MainController(self, False, self._lastSearch)
        else:
            pass

    def loadMD(self):
        pass


    def openTranslater(self):
        if INTERN:
            self._translater = SequenceTranslaterWindow()
        else:
            pass

def run():
    app = QApplication(sys.argv)
    app.setStyle(QtWidgets.QStyleFactory.create("Fusion"))
    app.setApplicationName("FAST MS")
    gui = Window()
    sys.exit(app.exec_())


if __name__ == '__main__':
    run()