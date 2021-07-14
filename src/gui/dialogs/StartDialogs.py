import traceback

from PyQt5 import QtWidgets, QtCore
from src import path
from os.path import join

from src.Exceptions import InvalidInputException
from src.Services import FragmentationService, ModificationService, SequenceService, IntactIonService
from src.gui.dialogs.AbstractDialogs import StartDialog, DialogWithTabs, AbstractDialog
from src.gui.GUI_functions import createComboBox
from src.gui.widgets.Widgets import OpenFileWidget
from src.repositories.ConfigurationHandler import ConfigurationHandlerFactory



class TDStartDialog(StartDialog):
    '''
    Dialog which pops up when top-down analysis is started. Values are stored in settings_top_down.json
    '''
    def __init__(self, parent):
        super().__init__(parent, "Settings")
        self._formLayout = self.makeFormLayout(self)
        self._configHandler = ConfigurationHandlerFactory.getTD_SettingHandler()
        self.setupUi()

    def setupUi(self):
        labelNames = ("Sequence Name:", "Charge:", "Fragmentation:", "Modifications:", "Nr. of Modifications:",
                           "Spectral Data:", "Noise Threshold (x10^6):", "Fragment Library:")
        fragPatterns = FragmentationService().getAllPatternNames()
        modPatterns = ModificationService().getAllPatternNames()
        sequences = SequenceService().getAllSequenceNames()
        widgets = {"sequName": (createComboBox(self,sequences), "Name of the sequence"),
                   "charge": (QtWidgets.QSpinBox(self), "Charge of the precursor ion"),
                    "fragmentation": (createComboBox(self,fragPatterns), "Name of the fragmentation - pattern"),
                    "modifications": (createComboBox(self,modPatterns), "Name of the modification/ligand - pattern"),
                    "nrMod": (QtWidgets.QSpinBox(self), "How often is the precursor ion modified?"),
                    "spectralData": (OpenFileWidget(self,1, join(path, 'Spectral_data','top-down'),
                                    "Open File","Plain Text Files (*txt);;Comma Separated Values (*csv);;All Files (*)"),
                                "Name of the file with spectral peaks (txt or csv format)\n"
                                 "If no file is stated, the program will just calculate the fragment library"),
                    'noiseLimit': (QtWidgets.QDoubleSpinBox(self), "Minimal noise level"),
                    "fragLib": (QtWidgets.QLineEdit(self), "Name of csv file in the folder 'Fragment_lists' "
                            "containing the isotope patterns of the fragments\n"
                            "If no file is stated, the program will search for the corresponing file or create a new one")}
               #(QtWidgets.QLineEdit(startDialog), "output",
                    #"Name of the output Excel file\ndefault: name of spectral pattern file + _out.xlsx"))
        index = self.fill(self, self._formLayout, labelNames, widgets)
        #xPos, yPos = self.createWidgets(widgets,200,linewidth)
        self._widgets['charge'].setMinimum(-99)
        self._widgets['noiseLimit'].setMinimum(0.01)
        self._widgets['modifications'].currentTextChanged.connect(self.changeNrOfMods)
        #self._buttonBox.setGeometry(QtCore.QRect(210, yPos+20, 164, 32))
        #self._widgets['_charge'].setValue(2)
        if self._configHandler.getAll() != None:
            try:
                self._widgets["fragmentation"].setCurrentText(self._configHandler.get('fragmentation'))
                self._widgets["modifications"].setCurrentText(self._configHandler.get('modifications'))
                self.changeNrOfMods()
                #self._widgets["nrMod"].setValue(self._configHandler.get('nrMod'))
            except KeyError:
                traceback.print_exc()
        #self.makeButtonBox(self)
        self._formLayout.addItem(QtWidgets.QSpacerItem(0,1))
        self._defaultButton = self.makeDefaultButton(self)
        self._formLayout.setWidget(index + 1, QtWidgets.QFormLayout.FieldRole, self._buttonBox)
        self._formLayout.setWidget(index+1, QtWidgets.QFormLayout.LabelRole, self._defaultButton)
        self.backToLast()

    def changeNrOfMods(self):
        if self._widgets['modifications'].currentText() == '-':
            self._widgets['nrMod'].setValue(0)
            self._widgets['nrMod'].setEnabled(False)
        elif 'nrMod' in self._configHandler.getAll().keys():
            self._widgets['nrMod'].setEnabled(True)
            self._widgets["nrMod"].setValue(self._configHandler.get('nrMod'))
        else:
            self._widgets['nrMod'].setEnabled(True)
            self._widgets["nrMod"].setValue(1)

    def backToLast(self):
        super(TDStartDialog, self).backToLast()
        self.setValueOfWidget(self._widgets['noiseLimit'], self._configHandler.get('noiseLimit') / 10 ** 6)

    def accept(self):
        settings = self.getNewSettings()
        if settings is not None:
            self._newSettings = settings
            self._newSettings['noiseLimit']*= 10 ** 6
            self._configHandler.write(self._newSettings)
            super(TDStartDialog, self).accept()


    def checkValues(self, configs, *args):
        return super(TDStartDialog, self).checkValues(configs, 'top-down')

    def checkSpectralDataFile(self, mode, fileName):
        if fileName == '':
            print('Just calculating fragment library')
            return False
        else:
            return super(TDStartDialog, self).checkSpectralDataFile(mode, fileName)


class IntactStartDialog(DialogWithTabs, StartDialog):
    '''
    Dialog which pops up when intact ion search is started. Values are stored in configurations_intact.json.
    '''
    def __init__(self, parent=None):
        super().__init__(parent,"Intact FragmentIon Search")
        self._configHandler = ConfigurationHandlerFactory.getIntactHandler()
        self.setupUi()

    def setupUi(self):
        self._settingTab = self.createTab("Settings")
        settingLayout = self.makeFormLayout(self._settingTab)
        self._configTab = self.createTab("Configurations")
        configLayout = self.makeFormLayout(self._configTab)
        modPatterns = IntactIonService().getAllPatternNames()
        sequences = SequenceService().getAllSequenceNames()
        self.fill(self._settingTab, settingLayout,
                  ("Sequence Name", "Modifications", "Spectral File", "Spray Mode", "Output"),
                  {"sequName": (createComboBox(self._settingTab,sequences), "Name of sequenceList"),
                   "modification": (createComboBox(self._settingTab,modPatterns), "Name of the modification pattern"),
                   "spectralData": (OpenFileWidget(self._settingTab, 1, join(path, 'Spectral_data', 'intact'), "Open File",
                                   "Plain Text Files (*txt);;All Files (*)"),
                                    "Name of the file with monoisotopic pattern (txt format)"),
                   "sprayMode": (createComboBox(self._settingTab, ("negative", "positive")), "Spray mode"),
                   "output": (QtWidgets.QLineEdit(self._settingTab),
                    "Name of the output txt file\ndefault: name of spectral pattern file + _out.txt")})
        if self._configHandler.getAll() != None:
            self._widgets['sprayMode'].setCurrentText(self._translate(self.objectName(), self._configHandler.get('sprayMode')))
        self.fill(self._configTab, configLayout,
                  ("min. m/z", "max. m/z", "max. raw error", "slope (k) of error", "intercept (d) of error"),
                  {"minMz": (QtWidgets.QSpinBox(), "m/z where search starts"),
                   "maxMz": (QtWidgets.QSpinBox(), "m/z where search ends"),
                   "errorLimitCalib": (QtWidgets.QSpinBox(), "max. ppm error in uncalbratied spectrum"),
                   "k": (QtWidgets.QDoubleSpinBox(),
                         "max. ppm error slope in calbratied spectrum (ppm = k/1000 + d)"),
                   "d": (QtWidgets.QDoubleSpinBox(),
                         "max. ppm error intercept in calbratied spectrum (ppm = k/1000 + d)")})
        self._widgets['minMz'].setMaximum(9999)
        self._widgets['maxMz'].setMaximum(9999)
        self._widgets["d"].setMinimum(-9.99)
        self.backToLast()
        self._verticalLayout.addWidget(self.makeButtonWidget(self), 0, QtCore.Qt.AlignRight)


    def makeButtonWidget(self, parent):
        widget = QtWidgets.QWidget(parent)
        horizontLayout = QtWidgets.QHBoxLayout(widget)
        self._buttonBox.setParent(widget)
        self._defaultButton = self.makeDefaultButton(widget)
        horizontLayout.addWidget(self._defaultButton)
        horizontLayout.addSpacing(50)
        horizontLayout.addWidget(self._buttonBox)
        return widget

    def accept(self):
        newSettings = self.getNewSettings()
        if newSettings is not None:
            self._configHandler.write(newSettings)
            super(IntactStartDialog, self).accept()


    def checkValues(self, configs, *args):
        return super(IntactStartDialog, self).checkValues(configs, 'intact')



class SpectrumComparatorStartDialog(AbstractDialog):
    '''
    Dialog which pops up when spectrum comparison is started.
    '''
    def __init__(self, parent):
        super().__init__(parent, "Compare Spectra")
        self._widgets = []
        self._verticalLayout = QtWidgets.QVBoxLayout(self)
        label1 = QtWidgets.QLabel(self)
        label1.setText(self._translate(self.objectName(),
                                      'Enter the file name containing the ions which you want to compare:'))
        self._verticalLayout.addWidget(label1)
        widget = QtWidgets.QWidget(self)
        horizLayout = QtWidgets.QHBoxLayout(widget)
        label2 = QtWidgets.QLabel(widget)
        label2.setText(self._translate(self.objectName(),'The format in the _files must be:\t"m/z   z   int.   name"\n'
                                                         '\t-with tab stops between each value'))
        horizLayout.addWidget(label2)
        self._startPath = join(path, 'Spectral_data', 'comparison')
        self._pushButton = QtWidgets.QPushButton(widget)
        self._pushButton.resize(52, 32)
        self._pushButton.setText(self._translate(self.objectName(), "+"))
        self._pushButton.clicked.connect(self.createInputWidget)
        horizLayout.addWidget(self._pushButton)
        self._verticalLayout.addWidget(widget)
        self._files = []
        for i in range(3):
            self.createInputWidget()
        self._verticalLayout.addWidget(self._buttonBox)
        self.show()

    def getFiles(self):
        return self._files

    def createInputWidget(self):
        widget = OpenFileWidget(self, 2, self._startPath, "Open File to Compare",
                                "Plain Text Files (*txt);;All Files (*)")
        widget.setToolTip("Names of text _files containing ion data")
        self._verticalLayout.removeWidget(self._buttonBox)
        self._verticalLayout.addWidget(widget)
        self._verticalLayout.addWidget(self._buttonBox)
        self._widgets.append(widget)
        widget.show()


    def accept(self):
        try:
            for widget in self._widgets:
                if widget.getFiles()!= ['']:
                    files = widget.getFiles()
                    for file in files:
                        self._files.append(self.checkSpectralDataFile('comparison',file))
            super(SpectrumComparatorStartDialog, self).accept()
        except InvalidInputException as e:
            traceback.print_exc()
            QtWidgets.QMessageBox.warning(self, "Problem occured", e.__str__(), QtWidgets.QMessageBox.Ok)




class OccupancyRecalcStartDialog(AbstractDialog):
    '''
    Dialog which pops up when occupancy calculation tool is started.
    '''
    def __init__(self, parent, sequences):
        super().__init__(parent, "Calculate Occupancies")
        self._sequence = None
        self._modification = None
        formLayout = self.makeFormLayout(self)
        index = self.fill(self, formLayout, ("Sequence Name: ", "Modification: "),
                          {"sequName": (createComboBox(self, sequences), "Name of the sequence"),
                           "modification": (QtWidgets.QLineEdit(self), "Name of the modification/ligand you want to "
                                           "search for.\nIf you want to search for a special number of modifications, "
                                              "enter the number as a prefix without any spaces")})
        formLayout.addItem(QtWidgets.QSpacerItem(0,1))
        formLayout.setWidget(index + 1, QtWidgets.QFormLayout.FieldRole, self._buttonBox)
        self.show()

    def getSequence(self):
        return self._sequence
    def getModification(self):
        return self._modification

    def accept(self):
        self._sequence = self._widgets['sequName'].currentText()
        self._modification = self._widgets['modification'].text()
        super(OccupancyRecalcStartDialog, self).accept()

