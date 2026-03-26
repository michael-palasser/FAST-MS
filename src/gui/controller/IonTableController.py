import traceback

from PyQt5 import QtWidgets

from src.Exceptions import InvalidInputException, InvalidIsotopePatternException
from src.entities.SearchSettings import SearchSettings
from src.gui.controller.AbstractController import AbstractMainController
from src.gui.dialogs.StartDialogs import TableStartDialog
from src.gui.tableviews.TableModels import TheoIonTableModel
from src.gui.tableviews.TableViews import TableView
from src.repositories.ConfigurationHandler import ConfigurationHandlerFactory
from src.repositories.IsotopePatternRepository import IsotopePatternRepository
from src.services.assign_services.TD_SpectrumHandler import SpectrumHandler
from src.services.library_services.FragmentLibraryBuilder import FragmentLibraryBuilder


class IonTableController(AbstractMainController):
    '''
    Controller class for starting, saving, exporting and loading a top-down search/analysis
    '''
    def __init__(self, parent, window):
        '''
        Starts either the search or loads a search from the database. Afterwards, result windows are shown.
        :param parent:
        :param (bool) new: True if new search, False if old search is loaded
        '''
        super().__init__(window)
        dialog = self.startDialog(parent)
        dialog.exec_()
        if dialog.canceled():
            return
        self._settings = dialog.newSettings()
        self._configs = ConfigurationHandlerFactory.getConfigHandler().getAll()
        self._propStorage = SearchSettings(self._settings['sequName'], self._settings['fragmentation'],
                                           self._settings['modifications'])
        self._saved = False
        try:
            if self.search() == 0:
                self.setUpUi()
        except InvalidInputException as e:
            traceback.print_exc()
            QtWidgets.QMessageBox.warning(None, "Problem occured", e.__str__(), QtWidgets.QMessageBox.Ok)

    @staticmethod
    def startDialog(parent):
        return TableStartDialog(parent)

    def search(self):
        '''
        Search for ions in spectrum: Calculates theo. isotope patterns, searches for these in the spectrum (peak list),
        models intensities, fixes problems by overlapping ions (2 user inputs possible for deleting ions)
        '''
        print("\n********** Creating fragment library **********")
        self._libraryBuilder = self.constructLibraryBuilder()
        self._libraryBuilder.createFragmentLibrary()
        """read existing ion-list file or create new one"""
        libraryImported = False
        patternReader = IsotopePatternRepository()
        settings = [self._settings[setting] for setting in ['sequName', 'fragmentation', 'nrMod', 'modifications']]
        if patternReader.findFile(settings):
            print("\n********** Importing list of isotope patterns from:", patternReader.getFile(), "**********")
            try:
                self._libraryBuilder.setFragmentLibrary(patternReader)
                libraryImported = True
                print("done")
            except InvalidIsotopePatternException:
                traceback.print_exc()
                choice = QtWidgets.QMessageBox.question(None, "Problem with importing list of isotope patterns",
                        "Imported Fragment Library from " + patternReader.getFile() + " incomplete<br>"
                        "Should a new library be created?<br>The search will be stopped otherwise",
                                                        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                if choice != QtWidgets.QMessageBox.Yes:
                    return 1
                    #sys.exit()
        if libraryImported == False:
            print("\n********** Writing new list of isotope patterns to:", patternReader.getFile(), "**********\n")
            #ld = LoadingWidget(len(self._libraryBuilder.getFragmentLibrary()), True)
            patternReader.saveIsotopePattern(self._libraryBuilder.addNewIsotopePattern())#ld.progress))
        """Importing spectral data"""
        constructor = self.getSpectrumHandlerConstructor()
        self._spectrumHandler = constructor(self._propStorage, self._libraryBuilder.getPrecursor(),self._settings,
                                                self._configs)
        allCharges = [z for z in range(abs(self._settings["charge"])+1)]
        self._monoIso, self._mostAb = [], []
        for fragName, vals in self._spectrumHandler.generateTheoreticIons(self._libraryBuilder.getFragmentLibrary()).items():
            rowMono, rowMostAb = [fragName], [fragName]
            for i in allCharges:
                if i in vals.keys():
                    rowMono.append(float(vals[i][0]))
                    rowMostAb.append(float(vals[i][1]))
                else:
                    rowMono.append("")
                    rowMostAb.append("")
            self._monoIso.append(rowMono)
            self._mostAb.append(rowMostAb)
        sprayMode = "+"
        if self._settings['charge'] < 0:
            sprayMode = "-"
        self._headers = ["Name", "Mass"] + [str(z)+sprayMode for z in allCharges[1:]]
        return 0

    def getSpectrumHandlerConstructor(self):
        return SpectrumHandler

    def constructLibraryBuilder(self):
        return FragmentLibraryBuilder(self._propStorage, self._settings['nrMod'], self._configs['maxIso'],
                                      self._configs['approxIso'])

    def setUpUi(self):
        self._layout = QtWidgets.QVBoxLayout(self._mainWindow.centralWidget())
        self._mainWindow.setWindowTitle("m/z Table")
        tabWidget = QtWidgets.QTabWidget(self._mainWindow.centralWidget())
        self._layout.addWidget(tabWidget)
        for name, data in {"monoisotopic":self._monoIso, "most abundant":self._mostAb}.items():
            tab = QtWidgets.QWidget()
            tabWidget.addTab(tab, name)
            layout = QtWidgets.QVBoxLayout(tab)
            scrollArea = QtWidgets.QScrollArea(tab)
            scrollArea.setWidgetResizable(True)
            model = TheoIonTableModel(self._headers, data)
            table = TableView(scrollArea, model)
            table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
            table.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
            table.resizeRowsToContents()
            table.resizeColumnsToContents()
            scrollArea.setWidget(table)
            layout.addWidget(scrollArea)
        # setIcon(self)
        self._mainWindow.show()