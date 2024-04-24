import traceback

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox

from src.resources import path, INTERN
from os.path import join

from src.Exceptions import InvalidInputException
from src.services.DataServices import FragmentationService, ModificationService, SequenceService, IntactIonService
from src.gui.dialogs.AbstractDialogs import StartDialog, AbstractDialog
from src.gui.GUI_functions import createComboBox, shoot
from src.gui.widgets.Widgets import OpenFileWidget
from src.repositories.ConfigurationHandler import ConfigurationHandlerFactory



class TDStartDialog(StartDialog):
    '''
    Dialog which pops up when top-down analysis is started. Values are stored in settings_top_down.json
    '''
    def __init__(self, parent):
        super().__init__(parent, "Settings")
        #self._formLayout = self.makeFormLayout(self)
        self._configHandler = ConfigurationHandlerFactory.getTD_SettingHandler()
        self.setupUi()
        shoot(self)

    def setupUi(self):
        '''widgets = self.getWidgets(SequenceService().getAllSequenceNames(),
                                  FragmentationService().getAllPatternNames(), ModificationService().getAllPatternNames())
               #(QtWidgets.QLineEdit(startDialog), "output",
                    #"Name of the output Excel file\ndefault: name of spectral pattern file + _out.xlsx"))
        index = self.fill(self, self._formLayout, self.getLabels(), widgets)'''
        super(TDStartDialog, self).setupUi(SequenceService().getAllSequenceNames(),
                                  FragmentationService().getAllPatternNames(), ModificationService().getAllPatternNames())
        #xPos, yPos = self.createWidgets(widgets,200,linewidth)
        #self._widgets['charge'].setMinimum(-99)
        #self.setValueOfWidget(self._widgets['charge'],self._configHandler.get('charge'))
        #self._widgets['noiseLimit'].setMinimum(0)
        self._widgets['noiseLimit'].setMaximum(99)
        self._widgets['noiseLimit'].setDecimals(5)
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
        '''self._formLayout.addItem(QtWidgets.QSpacerItem(0,1))
        self._defaultButton = self.makeDefaultButton(self)
        self._formLayout.setWidget(index + 1, QtWidgets.QFormLayout.FieldRole, self._buttonBox)
        self._formLayout.setWidget(index+1, QtWidgets.QFormLayout.LabelRole, self._defaultButton)'''
        self._widgets['calibration'].stateChanged.connect(lambda: self.updateCal(self._widgets['calibration'].isChecked()))
        self.updateCal(self._widgets['calibration'].isChecked())
        self.backToLast()

    def getLabels(self):
        return ("Sequence Name:", "Charge:", "Fragmentation:", "Modifications:", "No. of Modifications:",
                      "Spectral Data:", "Noise Threshold (x10^6):", 'Calibration:',
                      'Ions for Cal.:', 'Profile Spectrum:') # "Fragment Library:",

    def getWidgets(self, args):
        sequences, fragPatterns, modPatterns = args
        chargeWidget = QtWidgets.QSpinBox(self)
        chargeWidget.setMinimum(-99)
        widgets = {"sequName": (createComboBox(self,sequences), "Name of the sequence"),
                "charge": (chargeWidget, "Charge of the precursor ion"),
                "fragmentation": (createComboBox(self,fragPatterns), "Name of the fragmentation - pattern"),
                "modifications": (createComboBox(self,modPatterns), "Name of the modification/ligand - pattern"),
                "nrMod": (QtWidgets.QSpinBox(self), "How often is the precursor ion modified?"),
                "spectralData": (OpenFileWidget(self, 1, self.getDefaultDirectory("spectralData"),
                                "Open File","Plain Text Files (*txt);;Comma Separated Values (*csv);;All Files (*)"),
                            "Name of the file with spectral peaks (txt or csv format)\n"
                             "If no file is stated, the program will just calculate the fragment library"),
                'noiseLimit': (QtWidgets.QDoubleSpinBox(self), "Minimal noise level"),

                "calibration": (QtWidgets.QCheckBox(), "Spectral data will be calibrated if this option is ticked"),
                "calIons": (OpenFileWidget(self, 1, self.getDefaultDirectory("spectralData"), "Open Files",
                                            "Plain Text Files (*txt);;Comma Separated Values (*csv);;All Files (*)"),
                             "Name of the file with ions for calibration (txt format)"),}
        if INTERN:
            widgets["profile"] = (OpenFileWidget(self, 1, self.getDefaultDirectory("spectralData"),
                                           "Open File","xy File (*xy);;Plain Text Files (*txt);;Comma Separated Values (*csv);;All Files (*)"),
                           "Optional; name of the file containing the profile spectrum (xy, txt or csv format)")
        return widgets
        """return {"sequName": (createComboBox(self,sequences), "Name of the sequence"),
                "charge": (chargeWidget, "Charge of the precursor ion"),
                "fragmentation": (createComboBox(self,fragPatterns), "Name of the fragmentation - pattern"),
                "modifications": (createComboBox(self,modPatterns), "Name of the modification/ligand - pattern"),
                "nrMod": (QtWidgets.QSpinBox(self), "How often is the precursor ion modified?"),
                "spectralData": (OpenFileWidget(self, 1, self.getDefaultDirectory("spectralData"),
                                "Open File","Plain Text Files (*txt);;Comma Separated Values (*csv);;All Files (*)"),
                            "Name of the file with spectral peaks (txt or csv format)\n"
                             "If no file is stated, the program will just calculate the fragment library"),
                'noiseLimit': (QtWidgets.QDoubleSpinBox(self), "Minimal noise level"),

                "calibration": (QtWidgets.QCheckBox(), "Spectral data will be calibrated if this option is ticked"),
                "calIons": (OpenFileWidget(self, 1, self.getDefaultDirectory("spectralData"), "Open Files",
                                            "Plain Text Files (*txt);;Comma Separated Values (*csv);;All Files (*)"),
                             "Name of the file with ions for calibration (txt format)"),
                "profile": (OpenFileWidget(self, 1, self.getDefaultDirectory("spectralData"),
                                           "Open File","xy File (*xy);;Plain Text Files (*txt);;Comma Separated Values (*csv);;All Files (*)"),
                           "Optional; name of the file containing the profile spectrum (xy, txt or csv format)")}"""

    """"fragLib": (QtWidgets.QLineEdit(self), "If the fragment list has / should have a special name.\n"
                                           "If no file is stated, the program will search for the file with the standard name or create"
                                           " a new one with that name"),"""

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

    def getNewSettings(self):
        newSettings = self.makeDictToWrite()
        newSettings["fragLib"] = ""
        if (newSettings['spectralData'][-4:] != '.txt') and (newSettings['spectralData'][-4:] != '.csv') and (newSettings['spectralData']!=""):
            newSettings['spectralData'] += '.txt'
        try:
            newSettings = self.checkValues(newSettings)
            if newSettings['nrMod'] == 0:
                newSettings['modifications'] = '-'
            return newSettings
        except InvalidInputException as e:
            traceback.print_exc()
            QMessageBox.warning(self, "Problem occured", e.__str__(), QMessageBox.Ok)

    def checkValues(self, configs, *args):
        if self._widgets['charge'].value() == 0:
            raise InvalidInputException('Invalid Input','Charge must not be 0')
        if configs['calibration']:
            configs['calIons'] = self.checkSpectralDataFile('top-down', configs['calIons'])

        return super(TDStartDialog, self).checkValues(configs, 'top-down')

    """def checkSpectralDataFile(self, mode, fileName):
        if fileName == '':
            print('Just calculating fragment library')
            return ''
        else:
            return super(TDStartDialog, self).checkSpectralDataFile(mode, fileName)"""


class IntactStartDialog(StartDialog):
    '''
    Dialog which pops up when intact ion search is started. Values are stored in settings_intact.json.
    '''
    def __init__(self, parent=None, title="Assign Intact Ions", full= False):
        super().__init__(parent,title)
        if full:
            self._configHandler = ConfigurationHandlerFactory.getFullIntactHandler()
        else:
            self._configHandler = ConfigurationHandlerFactory.getIntactAssignHandler()
        self.setupUi()
        shoot(self)

    def setupUi(self):
        #self._formLayout = self.makeFormLayout(self)
        #widgets = self.getWidgets(SequenceService().getAllSequenceNames(), IntactIonService().getAllPatternNames())
        #index = self.fill(self, self._formLayout, self.getLabels(), widgets)
        index = super(IntactStartDialog, self).setupUi(SequenceService().getAllSequenceNames(), IntactIonService().getAllPatternNames())
        if self._configHandler.getAll() != None:
            self._widgets['sprayMode'].setCurrentText(self._translate(self.objectName(), self._configHandler.get('sprayMode')))
        #self.backToLast()

        '''self._formLayout.addItem(QtWidgets.QSpacerItem(0, 1))
        self._defaultButton = self.makeDefaultButton(self)
        self._formLayout.setWidget(index + 1, QtWidgets.QFormLayout.FieldRole, self._buttonBox)
        self._formLayout.setWidget(index + 1, QtWidgets.QFormLayout.LabelRole, self._defaultButton)'''
        #self._verticalLayout.addWidget(self.makeButtonWidget(self), 0, QtCore.Qt.AlignRight)

    def getLabels(self):
        return ["Sequence Name:", "Modifications:", "Spectral File:", "Spray Mode:", 'Input Mode:', "Min. m/z:", "Max. m/z:",
                 'Calibration:', "Output:"]

    def getWidgets(self, args):
        sequences, modPatterns = args
        return  {"sequName": (createComboBox(self, sequences), "Name of sequence"),
                 "modifications": (createComboBox(self, modPatterns), "Name of the modification pattern"),
                 "spectralData": (
                 OpenFileWidget(self, 2, join(path, 'Spectral_data', 'intact'), "Open Files",  # changed here
                                "Plain Text Files (*txt);;Comma Separated Values (*csv);;All Files (*)"),
                 "Name of the file with unassigned ions (txt format)"),
                 "sprayMode": (createComboBox(self, ("negative", "positive")), "Spray mode"),
                 "inputMode": (createComboBox(self, ("intensities", "abundances (int./z)")), "Are the intensities or "
                                                                                             "abundances stated in the third column of the data"),
                 "minMz": (self.getMinMaxWidget(), "m/z where search starts"),
                 "maxMz": (self.getMinMaxWidget(), "m/z where search ends"),
                 "calibration": (QtWidgets.QCheckBox(self), "Spectral data will be autocalibrated if this option is ticked"),
                 "output": (QtWidgets.QLineEdit(self),
                            "Name of the output txt file\ndefault: name of spectral pattern file + _out.txt")}

    def getMinMaxWidget(self):
        minMzWidget = QtWidgets.QSpinBox(self)
        minMzWidget.setMaximum(99999)
        return minMzWidget

    '''def makeButtonWidget(self, parent):
        widget = QtWidgets.QWidget(parent)
        horizontLayout = QtWidgets.QHBoxLayout(widget)
        self._buttonBox.setParent(widget)
        self._defaultButton = self.makeDefaultButton(widget)
        horizontLayout.addWidget(self._defaultButton)
        horizontLayout.addSpacing(50)
        horizontLayout.addWidget(self._buttonBox)
        return widget'''

    def accept(self):
        newSettings = self.getNewSettings()
        if newSettings is not None:
            self._configHandler.write(newSettings)
            super(IntactStartDialog, self).accept()


    def checkValues(self, configs, *args):
        return super(IntactStartDialog, self).checkValues(configs, 'intact')

    def checkSpectralDataFile(self, mode, fileName):
        files = []
        for file in fileName.split(',  '):
            files.append(super(IntactStartDialog, self).checkSpectralDataFile(mode, file))
        return files


class IntactStartDialogFull(IntactStartDialog):
    '''
    Dialog which pops up when full intact ion search is started. Values are stored in settings_intactFull.json.
    '''
    def __init__(self, parent=None):
        super().__init__(parent, "Full Intact Ion Search", ConfigurationHandlerFactory.getFullIntactHandler())
        self._configHandler = ConfigurationHandlerFactory.getFullIntactHandler()
        #self.setupUi()
        #self._widgets['noiseLimit'].setMinimum(0)
        self._widgets['noiseLimit'].setMaximum(999)
        self._widgets['noiseLimit'].setDecimals(3)
        self._widgets['calibration'].stateChanged.connect(lambda: self.updateCal(self._widgets['calibration'].isChecked()))
        self.updateCal(self._widgets['calibration'].isChecked())
        shoot(self)

    def getLabels(self):
        oldLabels = super(IntactStartDialogFull, self).getLabels()
        return oldLabels[:4] + ["Noise Threshold (x10^6):"] + oldLabels[5:8] + ['Ions for Cal.:', 'Profile Spectrum:']

    def getWidgets(self, args):
        sequences, modPatterns =args
        widgets = {"sequName": (createComboBox(self, sequences), "Name of sequence"),
                 "modifications": (createComboBox(self, modPatterns), "Name of the modification pattern"),
                 "spectralData": (
                    OpenFileWidget(self, 1, join(path, 'Spectral_data', 'intact'), "Open Files",
                                   "Plain Text Files (*txt);;Comma Separated Values (*csv);;All Files (*)"),
                    "Name of the file with peaks (txt format)"),
                 "sprayMode": (createComboBox(self, ("negative", "positive")), "Spray mode"),
                 'noiseLimit': (QtWidgets.QDoubleSpinBox(self), "Minimal noise level"),
                 "minMz": (self.getMinMaxWidget(), "m/z where search starts"),
                 "maxMz": (self.getMinMaxWidget(), "m/z where search ends"),
                 "calibration": (QtWidgets.QCheckBox(self), "Spectral data will be calibrated if this option is ticked"),
                 "calIons": (OpenFileWidget(self, 1, join(path, 'Spectral_data', 'intact'), "Open Files",
                                            "Plain Text Files (*txt);;Comma Separated Values (*csv);;All Files (*)"),
                             "Name of the file with ions for calibration (txt format)")}
        if INTERN:
            widgets["profile"] = (OpenFileWidget(self, 1, self.getDefaultDirectory("spectralData"),
                                           "Open File","xy File (*xy);;Plain Text Files (*txt);;Comma Separated Values (*csv);;All Files (*)"),
                           "Optional; name of the file containing the profile spectrum (xy, txt or csv format)")
        return widgets

    def backToLast(self):
        super(IntactStartDialogFull, self).backToLast()
        self.setValueOfWidget(self._widgets['noiseLimit'], self._configHandler.get('noiseLimit') / 10 ** 6)

    def accept(self):
        settings = self.getNewSettings()
        if settings is not None:
            self._newSettings = settings
            self._newSettings['noiseLimit']*= 10 ** 6
            self._configHandler.write(self._newSettings)
            super(IntactStartDialogFull, self).accept()

    def checkSpectralDataFile(self, mode, fileName):
        return super(IntactStartDialog, self).checkSpectralDataFile(mode, fileName)


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
        shoot(self)

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

