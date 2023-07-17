import traceback
from PyQt5 import QtWidgets

from src.Exceptions import InvalidInputException
from src.gui.GUI_functions import createComboBox
from src.gui.dialogs.AbstractDialogs import StartDialog
from src.gui.widgets.Widgets import OpenFileWidget
from src.repositories.ConfigurationHandler import ConfigurationHandlerFactory
from src.services.DataServices import FragmentationService, ModificationService, SequenceService


class MDStartDialog(StartDialog):
    '''
    Dialog which pops up when top-down analysis is started. Values are stored in settings_top_down.json
    '''
    def __init__(self, parent):
        super().__init__(parent, "Settings")
        self._configHandler = ConfigurationHandlerFactory.getMDHandler()
        self.setupUi()

    def setupUi(self):
        super(MDStartDialog, self).setupUi(SequenceService().getAllSequenceNames(),
                                  FragmentationService().getAllPatternNames(), ModificationService().getAllPatternNames())
        self._widgets['modifications'].currentTextChanged.connect(self.changeNrOfMods)
        if self._configHandler.getAll() != None:
            try:
                self._widgets["fragmentation"].setCurrentText(self._configHandler.get('fragmentation'))
                self._widgets["modifications"].setCurrentText(self._configHandler.get('modifications'))
                self.changeNrOfMods()
            except KeyError:
                traceback.print_exc()

    def getLabels(self):
        return ("Sequence Name:", "Charge:", "Fragmentation:", "Modifications:", "No. of Modifications:",
                      "Ion Data:", "Peak Data:", "Internal Calibration",'Output:')

    def getWidgets(self, args):
        sequences, fragPatterns, modPatterns = args
        chargeWidget = QtWidgets.QSpinBox(self)
        chargeWidget.setMinimum(-99)
        return {"sequName": (createComboBox(self,sequences), "Name of the sequence"),
                   "charge": (chargeWidget, "Charge of the precursor ion"),
                    "fragmentation": (createComboBox(self,fragPatterns), "Name of the fragmentation pattern"),
                    "modifications": (createComboBox(self,modPatterns), "Name of the modification/ligand pattern"),
                    "nrMod": (QtWidgets.QSpinBox(self), "How often is the precursor ion modified?"),
                    "snapData": (OpenFileWidget(self, 1, self.getDefaultDirectory("snapData"),
                                    "Open File","Plain Text Files (*txt);;Comma Separated Values (*csv);;All Files (*)"),
                                "Name of the file with the ion data (SNAP or similar) (txt or csv format)"),
                    "spectralData": (OpenFileWidget(self, 1, self.getDefaultDirectory("spectralData"),
                                    "Open File","Plain Text Files (*txt);;Comma Separated Values (*csv);;All Files (*)"),
                                "Name of the file with spectral peaks (txt or csv format)"),
                    "calibration": (QtWidgets.QCheckBox(self), "The peak and ion data will be internally calibrated if "
                                                               "this option is ticked"),
                    "output": (QtWidgets.QLineEdit(self),
                            "Name of the output txt file\ndefault: name of the Peak data file + _out.txt")}


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

    def accept(self):
        settings = self.getNewSettings()
        if settings is not None:
            self._newSettings = settings
            self._configHandler.write(self._newSettings)
            super(MDStartDialog, self).accept()

    def getNewSettings(self):
        newSettings = self.makeDictToWrite()
        if (newSettings['spectralData'][-4:] != '.txt') and (newSettings['spectralData'][-4:] != '.csv') and (newSettings['spectralData']!=""):
            newSettings['spectralData'] += '.txt'
        try:
            newSettings = self.checkValues(newSettings)
            if newSettings['nrMod'] == 0:
                newSettings['modifications'] = '-'
            return newSettings
        except InvalidInputException as e:
            traceback.print_exc()
            QtWidgets.QMessageBox.warning(self, "Problem occured", e.__str__(), QtWidgets.QMessageBox.Ok)

    def checkValues(self, configs, *args):
        if self._widgets['charge'].value() == 0:
            raise InvalidInputException('Invalid Input','Charge must not be 0')
        configs['snapData'] = self.checkSpectralDataFile('top-down', configs['snapData'])
        return super(MDStartDialog, self).checkValues(configs, 'top-down')

    """def checkSpectralDataFile(self, mode, fileName):
        if fileName == '':
            print('Just calculating fragment library')
            return ''
        else:
            return super(MDStartDialog, self).checkSpectralDataFile(mode, fileName)"""



class MD_ScoreParameterDialog(StartDialog):
    def __init__(self) -> None:
        super().__init__(None, "Penalties and Rewards")
        self._configHandler = ConfigurationHandlerFactory.getMDScoresHandler()
        self.setupUi()
        self.show()

    def getLabels(self):
        return ('S/N Penalty:', 'Error Penalty:', 'Co-isolation Penalty:',
                'I (FAST MS):', 'S/N (FAST MS):', 'quality (FAST MS):', 
                'I (SNAP):', 'S/N (SNAP):', 'quality factor (SNAP):', 
                'I (peak):', 'S/N (peak):')


    def getWidgets(self, args):
        widgetDict = {"pen_S/N": (QtWidgets.QDoubleSpinBox(self), "Penalty for a S/N < 10 (peak or SNAP)"),
                      "pen_error": (QtWidgets.QDoubleSpinBox(self), "Penalty for a mass error > 5 ppm (peak)"),
                      "pen_prec": (QtWidgets.QDoubleSpinBox(self), "Penalty if the ion is next to the precursor (+/- 5 Da)"),
                      "I": (QtWidgets.QDoubleSpinBox(self), "Reward for a high intensity"),
                      "S/N": (QtWidgets.QDoubleSpinBox(self), "Reward for a S/N"),
                      "quality": (QtWidgets.QDoubleSpinBox(self), "Reward for a high quality"),
                      "I_SNAP": (QtWidgets.QDoubleSpinBox(self), "Reward for a high intensity (SNAP)"),
                      "S/N_SNAP": (QtWidgets.QDoubleSpinBox(self), "Reward for a high S/N (SNAP)"),
                      "quality_SNAP": (QtWidgets.QDoubleSpinBox(self), "Reward for a high quality factor (SNAP)"),
                      "I_mono": (QtWidgets.QDoubleSpinBox(self), "Reward for a high intensity (SNAP)"),
                      "S/N_mono": (QtWidgets.QDoubleSpinBox(self), "Reward for a high S/N of the monoisotopic peak in peak list")}
        for key, tup in widgetDict.items():
            if key.startswith('pen_'):
                tup[0].setMinimum(-99)
                tup[0].setMaximum(0)
            else:
                tup[0].setMinimum(0)
                tup[0].setMaximum(99)
            tup[0].setDecimals(1)
        return widgetDict

    def accept(self):
        settings = self.makeDictToWrite()
        if settings is not None:
            self._newSettings = settings
            self._configHandler.write(self._newSettings)
            super(MD_ScoreParameterDialog, self).accept()
