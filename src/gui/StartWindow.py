'''
Created on 20 Oct 2020

@author: michael
'''
import logging
import sys
import traceback

from PyQt5 import QtWidgets
from PyQt5.QtCore import QSize

from src.Exceptions import CanceledException, InvalidInputException
from src.gui.GUI_functions import setIcon
from src.gui.mainWindows.AbstractMainWindows import SimpleMainWindow
from src.top_down.SpectrumComparator import run as spectrumComparator


class Window(SimpleMainWindow):
    '''
    Main window which pops up when FAST MS is started
    '''
    def __init__(self):
        super(Window, self).__init__(None, 'FAST MS - Home')
        self._layout = QtWidgets.QHBoxLayout(self._centralwidget)
        self._layout.setContentsMargins(25,10,25,25)
        self.createMenuBar()
        self.createMenu('Top-Down',
                        {'Analyse Spectrum':
                             (lambda:self.startTopDown(True), 'Starts analysis of top-down spectrum', None),
                         'Load Analysis':
                             (lambda:self.startTopDown(False), 'Loads an old analysis', None),
                         "Get m/z's":
                             (self.startTable, "Calculates theoretic m/z's", None),
                         #'Reopen Current Analysis':
                         #    (self.reopen, 'Re-opens the last analysis', None),
                         #'Calc. Abundances':
                         #    (lambda: modellingTool(self), 'Calculates relative abundances of an ion list', None),
                         #'Localise Modification':
                         #    (lambda: occupancyRecalculator(self), 'Calculates the modified proportions for each fragment based on a given (fragment) ion list', None),
                         }, None)
        #[print(action.toolTip()) for action in menuActions.values()]
        #print(menu.toolTipsVisible())
        self.createMenu('Intact Ions',
                        {'Analyse Spectrum': (
                        lambda: self.startIntact(True), 'Starts analysis of intact ion spectrum', None),
                         'Assign Intact Ions': (lambda: self.editData(self.startIntactIonSearch),
                                                 'Starts assignment and analysis of lists with unfragmented ions', None),
                         'Edit Intact Ions': (
                         lambda: self.editData("intact"), 'Edit Intact Ions', None)}, None)
        self.createMenu('Other Tools',
                        {'Model Ion':
                             (self.openIonModeller, 'Calculates the isotope pattern of an ion', None),
                         'Compare Ion Lists':
                             (lambda: self.startApp(spectrumComparator, self), 'Compares ion lists of multiple spectra', None)},None)

        self.addAdditionalMenu()
        self.createMenu('Edit',
                        {'Configurations':(self.editTopDownConfig, 'Edit configurations', None),
                         'Elements': (lambda: self.editData("element"), 'Edit element table', None),
                         'Molecules': (lambda: self.editData("molecule"), 'Edit Molecular Properties', None),
                         'Sequences': (lambda: self.editData("sequence"), 'Edit stored sequences', None),
                         'Fragments': (lambda: self.editData("fragment"), 'Edit fragment patterns', None),
                         'Modifications': (lambda: self.editData("modification"),
                                           'Edit modification/ligand patterns',None)},
                        None)
        self.makeHelpMenu()
        self.move(200,200)
        # self.setWindowIcon(QIcon('pic.png'))
        self._lastSearch = None
        self.showButtons()
        self._openWindows=[]
        self.show()

    def showButtons(self):
        #layout1 = QtWidgets.QVBoxLayout(self._centralwidget)
        btnWidget1 = QtWidgets.QWidget(self._centralwidget)
        btnLayout1 = QtWidgets.QVBoxLayout(btnWidget1)
        self._layout.addWidget(btnWidget1)
        self.makeButton(btnWidget1, btnLayout1, 'Starts analysis of top-down spectrum',
                              lambda:self.startTopDown(True), "msms.png")
        self.makeButton(btnWidget1, btnLayout1, "Calculates theoretic fragment ion m/z's",
                              self.startTable, "table.png")
        #self._layout.setSpacing(30)
        btnWidget2 = QtWidgets.QWidget(self._centralwidget)
        btnLayout2 = QtWidgets.QVBoxLayout(btnWidget2)
        self.makeButton(btnWidget2, btnLayout2, 'Starts analysis of intact ion spectrum',
                              self.startIntact, "esi.png")
        self.makeButton(btnWidget2, btnLayout2, 'Calculates the isotope pattern of an ion',
                              self.openIonModeller, "modelIon.png")
        self._layout.addWidget(btnWidget2)
        return btnWidget1, btnLayout1, btnWidget2, btnLayout2

    def startTopDown(self, new):
        from src.gui.controller.TD_searchController import TD_MainController
        self._lastSearch = SimpleMainWindow(None, '')
        self.startApp(TD_MainController, self, new, self._lastSearch)
        """try:
            TD_MainController(self, new, self._lastSearch)
        except Exception as e:
            logging.exception(e.__str__())
            raise e"""

    def startTable(self):
        from src.gui.controller.IonTableController import IonTableController
        self._tableWindow = SimpleMainWindow(None, '')
        self.startApp(IonTableController, self, self._tableWindow)

    def startIntact(self, new):
        from src.gui.controller.IntactSearchController import IntactMainController
        self._lastSearch = SimpleMainWindow(None, '')
        self.startApp(IntactMainController, self, new, self._lastSearch)
        #IntactMainController(self, new, self._lastSearch)

    def reopen(self):
        if self._lastSearch is not None:
            self._lastSearch.show()

    def makeButton(self, parent, layout, toolTip, fun, image=None):
        btn = QtWidgets.QPushButton(parent)
        btn.setToolTip(toolTip)
        btn.clicked.connect(fun)
        btn.setMinimumSize(QSize(200, 150))
        layout.addWidget(btn)
        if image is not None:
            """abs_path = os.path.join(base_path, "src", "gui","icons", image)
            btn.setIcon(QIcon(abs_path))"""
            #btn.setIcon(QIcon(f":/icons/{image}"))
            setIcon(btn,image)
            btn.setIconSize(QSize(200, 150))
            btn.setFlat(True)
            btn.setAutoFillBackground(True)
        return btn


    def startIntactIonSearch(self):
        from src.gui.dialogs.StartDialogs import IntactStartDialog
        from src.intact.Main import run as IntactIonsSearch
        dialog = IntactStartDialog(self)
        if dialog.exec_() and dialog.ok:
            self.startApp(IntactIonsSearch)
            """IntactIonsSearch()
            except InvalidInputException as e:
                traceback.print_exc()
                QtWidgets.QMessageBox.warning(self, "Problem occured", e.__str__(), QtWidgets.QMessageBox.Ok)"""

    def openIonModeller(self):
        from src.gui.controller.IsotopePatternView import IsotopePatternView
        self._openWindows.append(IsotopePatternView(None))

    """
    def compareSpectra(self):
        self.startApp(spectrumComparator)
       try:
            spectrumComparator(self)
        except InvalidInputException as e:
            traceback.print_exc()
            QtWidgets.QMessageBox.warning(self, "Problem occured", e.__str__(), QtWidgets.QMessageBox.Ok)"""


    def close_application(self):
        print('exit')
        sys.exit()

    def editTopDownConfig(self):
        from src.gui.dialogs.ParameterDialogs import ConfigurationDialog
        dialog = ConfigurationDialog(self)
        dialog.exec_()

    def editData(self, controller):
        from src.gui.controller.EditorController import IntactIonEditorController, ElementEditorController, \
            MoleculeEditorController, SequenceEditorController, FragmentEditorController, ModificationEditorController
        d = {"element":ElementEditorController, "molecule": MoleculeEditorController, "sequence":SequenceEditorController,
             "fragment":FragmentEditorController, "modification":ModificationEditorController, "intact":IntactIonEditorController}
        try:
            self._openWindows.append(d[controller]())
        except CanceledException:
            pass
        except InvalidInputException as e:
            traceback.print_exc()
            QtWidgets.QMessageBox.warning(self, "Problem occured", e.__str__(), QtWidgets.QMessageBox.Ok)

    def addAdditionalMenu(self):
        pass

    @staticmethod
    def startApp(app, *args):
        try:
            app(*args)
        except Exception as e:
            traceback.print_exc()
            logging.exception(e.__str__())
            QtWidgets.QMessageBox.warning(None, "Problem occured", e.__str__(), QtWidgets.QMessageBox.Ok)
            raise e

"""def run():
    app = QApplication(sys.argv)
    app.setStyle(QtWidgets.QStyleFactory.create("Fusion"))
    app.setApplicationName("FAST MS")
    setIcon(app)
    if INTERN:
        gui = InternalWindow()
    else:
        gui = Window()
    sys.exit(app.exec_())


if __name__ == '__main__':
    run()"""