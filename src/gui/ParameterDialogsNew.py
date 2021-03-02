import traceback

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QFileDialog
from os.path import join, isfile

from src import path
from src.Exceptions import UnvalidInputException
from src.repositories.ConfigurationHandler import ConfigurationHandlerFactory
from src.Services import FragmentIonService, ModificationService, SequenceService
from src.gui.StartDialogs import OpenFileWidget

dataPath = join(path, 'src', 'data')

class AbstractDialog(QtWidgets.QDialog):
    def __init__(self, parent, title):
        super().__init__(parent)
        #self.setObjectName(dialogName)
        #self.lineSpacing = lineSpacing
        self.widgets = dict()
        #self.sizePolicy = self.setNewSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self._translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(self._translate(self.objectName(), title))


        self._widgetSizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self._widgetSizePolicy.setHorizontalStretch(0)
        self._widgetSizePolicy.setVerticalStretch(0)
        self.makeButtonBox(self)
        self.newSettings = None
        self.move(300,100)
        self.canceled = False

    @staticmethod
    def setNewSizePolicy(horizontal, vertical):
        sizePolicy = QtWidgets.QSizePolicy(horizontal, vertical)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        return sizePolicy

    def makeFormLayout(self, parent):
        formLayout = QtWidgets.QFormLayout(parent)
        formLayout.setHorizontalSpacing(12)
        #formLayout.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        formLayout.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)
        formLayout.setLabelAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        formLayout.setFormAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        return formLayout

    def fill(self, parent, formLayout, labelNames, widgets, *args):
        index = 0
        for labelName, key in zip(labelNames, widgets.keys()):
            self.makeLine(parent, formLayout, index, labelName, key, widgets[key], args)
            index += 1
        return index

    def makeLine(self, parent, formLayout, yPos, labelName, widgetName, widgetTuple, *args):
        label = QtWidgets.QLabel(parent)
        label.setText(self._translate(self.objectName(), labelName))
        widget = widgetTuple[0]
        if args and args[0]:
            label.setMinimumWidth(args[0][0])
            widget.setMaximumWidth(args[0][1])
        formLayout.setWidget(yPos, QtWidgets.QFormLayout.LabelRole, label)
        widget.setParent(parent)
        widget.setObjectName(widgetName)
        widget.setToolTip(self._translate(self.objectName(), widgetTuple[1]))
        self._widgetSizePolicy.setHeightForWidth(widget.sizePolicy().hasHeightForWidth())
        widget.setSizePolicy(self._widgetSizePolicy)
        self.widgets[widgetName] = widget
        formLayout.setWidget(yPos, QtWidgets.QFormLayout.FieldRole, widget)

    def createComboBox(self, parent, options):
        comboBox = QtWidgets.QComboBox(parent)
        for i, option in enumerate(options):
            comboBox.addItem("")
            comboBox.setItemText(i, self._translate(self.objectName(), option))
        return comboBox

    def makeButtonBox(self, parent):
        self.buttonBox = QtWidgets.QDialogButtonBox(parent)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        return self.buttonBox


    @staticmethod
    def getValueOfWidget(widget):
        if isinstance(widget, QtWidgets.QSpinBox) or isinstance(widget, QtWidgets.QDoubleSpinBox):
            return widget.value()
        elif isinstance(widget, QtWidgets.QLineEdit) or isinstance(widget, OpenFileWidget):
            return widget.text()
        elif isinstance(widget, QtWidgets.QComboBox):
            return widget.currentText()
        else:
            raise Exception('Unknown type of widget')

    @staticmethod
    def setValueOfWidget(widget, value):
        if isinstance(widget, QtWidgets.QSpinBox) or isinstance(widget, QtWidgets.QDoubleSpinBox):
            widget.setValue(value)
        elif isinstance(widget, QtWidgets.QLineEdit) or isinstance(widget, OpenFileWidget):
            widget.setText(value)
        elif isinstance(widget, QtWidgets.QComboBox):
            widget.setCurrentText(value)
        else:
            raise Exception('Unknown type of widget')


    def backToLast(self):
        if self.configHandler.getAll()!=None:
            for name, item in self.widgets.items():
                self.setValueOfWidget(item, self.configHandler.get(name))

    def reject(self):
        self.canceled = True
        super(AbstractDialog, self).reject()

    def makeDictToWrite(self):
        newSettings = dict()
        for name, item in self.widgets.items():
            newSettings[name] = self.getValueOfWidget(item)
        return newSettings


    def accept(self):
        self.ok = True
        print(self.newSettings)
        super(AbstractDialog, self).accept()

    def checkValues(self, configs):
        pass


class StartDialog(AbstractDialog):
    def __init__(self, parent, title):
        super(StartDialog, self).__init__(parent, title)

    """def startProgram(self, mainMethod):
        self.makeDictToWrite()
        #try:
        mainMethod()"""
        #    super(StartDialog, self).accept()
        #except:
        #    traceback.print_exc()
         #   QMessageBox.warning(self, "Problem occured", traceback.format_exc(), QMessageBox.Ok)

    '''def makeButtonWidget(self, parent):
        widget = QtWidgets.QWidget(parent)
        horizontLayout = QtWidgets.QHBoxLayout(widget)
        self.makeButtonBox(widget)
        self.defaultButton = self.makeDefaultButton(widget)
        horizontLayout.addWidget(self.defaultButton)
        horizontLayout.addSpacing(50)
        horizontLayout.addWidget(self.buttonBox)
        return widget'''

    def makeDefaultButton(self, parent):
        self._defaultButton = QtWidgets.QPushButton(parent)
        sizePolicy = self.setNewSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHeightForWidth(self._defaultButton.sizePolicy().hasHeightForWidth())
        self._defaultButton.setSizePolicy(sizePolicy)
        self._defaultButton.setMinimumSize(QtCore.QSize(113, 0))
        self._defaultButton.clicked.connect(self.backToLast)
        self._defaultButton.setText(self._translate(self.objectName(), "last settings"))
        return self._defaultButton

    def getNewSettings(self):
        newSettings = self.makeDictToWrite()
        if (newSettings['spectralData'][-4:] != '.txt') and (newSettings['spectralData'][-4:] != '.csv') and (newSettings['spectralData']!=""):
            newSettings['spectralData'] += '.txt'
        try:
            newSettings = self.checkValues(newSettings)
        except UnvalidInputException as e:
            traceback.print_exc()
            QMessageBox.warning(self, "Problem occured", e.__str__(), QMessageBox.Ok)
        return newSettings

    def checkValues(self, configs, *args):
        if configs['sequName'] not in SequenceService().getAllSequenceNames():
            raise UnvalidInputException(configs['sequName'], "not found")
        if self.checkSpectralDataFile(args[0], configs['spectralData']):
            configs['spectralData'] = join(path, 'Spectral_data', args[0], configs['spectralData'])
        return configs


    def checkSpectralDataFile(self, mode, fileName):
        #spectralDataPath = join(path, 'Spectral_data',mode, fileName)
        if not isfile(fileName):
            spectralDataPath = join(path, 'Spectral_data', mode, fileName)
            if isfile(spectralDataPath):
                return True
            else:
                raise UnvalidInputException(spectralDataPath, "not found")
        return False


class TDStartDialog(StartDialog):
    def __init__(self, parent):
        super().__init__(parent, "Settings")
        self._formLayout = self.makeFormLayout(self)
        self.configHandler = ConfigurationHandlerFactory.getTD_SettingHandler()
        self.setupUi()

    def setupUi(self):
        labelNames = ("Sequence Name:", "Charge:", "Fragmentation:", "Modifications:", "Nr. of Modifications:",
                           "Spectral Data:", "Noise Threshold (x10^6):", "Fragment Library:")
        fragPatterns = FragmentIonService().getAllPatternNames()
        modPatterns = ModificationService().getAllPatternNames()
        sequences = SequenceService().getAllSequenceNames()
        widgets = {"sequName": (self.createComboBox(self,sequences), "Name of the sequence"),
                   "charge": (QtWidgets.QSpinBox(self), "Charge of the precursor ion"),
                    "fragmentation": (self.createComboBox(self,fragPatterns), "Name of the fragmentation - pattern"),
                    "modifications": (self.createComboBox(self,modPatterns), "Name of the modification/ligand - pattern"),
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
        self.widgets['charge'].setMinimum(-99)
        self.widgets['noiseLimit'].setMinimum(0.01)
        self.widgets['modifications'].currentTextChanged.connect(self.changeNrOfMods)
        #self.buttonBox.setGeometry(QtCore.QRect(210, yPos+20, 164, 32))
        #self.widgets['charge'].setValue(2)
        if self.configHandler.getAll() != None:
            try:
                self.widgets["fragmentation"].setCurrentText(self.configHandler.get('fragmentation'))
                self.widgets["modifications"].setCurrentText(self.configHandler.get('modifications'))
                self.changeNrOfMods()
                #self.widgets["nrMod"].setValue(self.configHandler.get('nrMod'))
            except KeyError:
                traceback.print_exc()
        #self.makeButtonBox(self)
        self._formLayout.addItem(QtWidgets.QSpacerItem(0,1))
        self.defaultButton = self.makeDefaultButton(self)
        self._formLayout.setWidget(index+1, QtWidgets.QFormLayout.FieldRole, self.buttonBox)
        self._formLayout.setWidget(index+1, QtWidgets.QFormLayout.LabelRole, self._defaultButton)

    def changeNrOfMods(self):
        if self.widgets['modifications'].currentText() == '-':
            self.widgets['nrMod'].setValue(0)
            self.widgets['nrMod'].setEnabled(False)
        elif 'nrMod' in self.configHandler.getAll().keys():
            self.widgets['nrMod'].setEnabled(True)
            self.widgets["nrMod"].setValue(self.configHandler.get('nrMod'))
        else:
            self.widgets['nrMod'].setEnabled(True)
            self.widgets["nrMod"].setValue(1)


    def backToLast(self):
        super(TDStartDialog, self).backToLast()
        self.setValueOfWidget(self.widgets['noiseLimit'], self.configHandler.get('noiseLimit') / 10**6)

    def accept(self):
        self.newSettings = self.getNewSettings() #self.makeDictToWrite()
        #self.checkValues(newSettings)
        self.newSettings['noiseLimit']*=10**6
        self.configHandler.write(self.newSettings)
        print(self.newSettings)
        #self.newSettings = newSettings
        #self.startProgram(Main.run)
        super(TDStartDialog, self).accept()


    def checkValues(self, configs, *args):
        return super(TDStartDialog, self).checkValues(configs, 'top-down')

    def checkSpectralDataFile(self, mode, fileName):
        if fileName == '':
            print('Just calculating fragment library')
            return False
        else:
            super(TDStartDialog, self).checkSpectralDataFile(mode, fileName)


class DialogWithTabs(AbstractDialog):
    def __init__(self, parent, title):
        super().__init__(parent, title)
        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setContentsMargins(0,12,0,12)
        #self.verticalLayout.setObjectName("verticalLayout")
        self.tabWidget = QtWidgets.QTabWidget(self)
        self.tabWidget.setEnabled(True)
        tabSizePolicy = self.setNewSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        tabSizePolicy.setHeightForWidth(self.tabWidget.sizePolicy().hasHeightForWidth())
        self.tabWidget.setSizePolicy(tabSizePolicy)
        self.verticalLayout.addWidget(self.tabWidget)


        #self.sizePolicy.setHeightForWidth(self.buttonBox.sizePolicy().hasHeightForWidth())
        #self.buttonBox.setSizePolicy(self.sizePolicy)
        #self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)


    def createTab(self,name):
        tab = QtWidgets.QWidget(self)
        verticalLayout = QtWidgets.QVBoxLayout(tab)
        self.tabWidget.addTab(tab, "")
        self.tabWidget.setTabText(self.tabWidget.indexOf(tab), self._translate(self.objectName(), name))
        tab.setLayout(verticalLayout)
        return tab


class TD_configurationDialog(DialogWithTabs):
    def __init__(self, parent):
        super().__init__(parent, "Configurations")
        self.configHandler = ConfigurationHandlerFactory.getTD_ConfigHandler()
        self.interestingIons = list()
        self.tabs = dict()
        self._boxSizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.setupUi(self)
        self.verticalLayout.addWidget(self.buttonBox, 0, QtCore.Qt.AlignRight)


    def fillBox(self, parent, title, labels, widgets):
        #height = (len(labels)+1)*self.lineSpacing
        box = QtWidgets.QGroupBox(parent)
        box.setSizePolicy(self._boxSizePolicy)
        box.setTitle(self._translate(self.objectName(), title))
        #box.setGeometry(QtCore.QRect(5, yPos, 320, height))
        box.setAutoFillBackground(False)
        formLayout = self.makeFormLayout(box)
        self.fill(box, formLayout, labels, widgets, 200, 70)
        parent.layout().addWidget(box)
        return box
        #self.createLabels(labels, box, 10, 200)
        #self.createWidgets(widgets,240,70)
        #return yPos+height

    def fillInterestingIonsBox(self, parent):
        box = QtWidgets.QGroupBox(parent)
        box.setGeometry(QtCore.QRect(5, 10, 320, 90))
        box.setTitle(self._translate(self.objectName(), "interesting ions"))
        box.setToolTip(self._translate(self.objectName(), "tick fragment types which should be more deeply analysed"))
        count = 0
        for key in ('a', 'b', 'c', 'd', 'w', 'x', 'y', 'z'):
            checkbox = QtWidgets.QCheckBox(box)
            if count < 4:
                checkbox.setGeometry(QtCore.QRect(10+int(count/2)*70, 30+(count%2)*30 , 50, 20))
            else:
                checkbox.setGeometry(QtCore.QRect(60+int(count/2)*70, 30+(count%2)*30 , 50, 20))
            checkbox.setText(self._translate("configDialog", key))
            checkbox.setObjectName(key)
            self.interestingIons.append(checkbox)
            count +=1
        parent.layout().addWidget(box)
        return box


    def setupUi(self, configDialog):
        configDialog.move(200,100)
        self.spectrumTab = self.createTab("spectrum")
        self.threshold1Tab = self.createTab("thresholds 1")
        self.threshold2Tab = self.createTab("thresholds 2")
        self.outputTab = self.createTab("analysis/output")
        #self.mzBox = QtWidgets.QGroupBox(self.spectrumTab)
        self.mzBox = self.fillBox(self.spectrumTab, "m/z area containing peaks", ("min. m/z", "min. max. m/z", "tolerance", "window size"),
                         {"lowerBound": (QtWidgets.QSpinBox(),
                                         "lower m/z bound (just peaks with higher m/z are examined)"),
                          "minUpperBound":(QtWidgets.QSpinBox(), "minimal upper m/z bound"),
                          "upperBoundTolerance": (QtWidgets.QSpinBox(),
                                                "value is added to calculated upper m/z-bound for final value"),
                          "upperBoundWindowSize": (QtWidgets.QDoubleSpinBox(),
                                                   "window size for noise calculation to find upper m/z bound")})
        self.widgets['lowerBound'].setMaximum(9999)
        self.widgets['minUpperBound'].setMaximum(9999)
        self.widgets['upperBoundTolerance'].setMaximum(999)

        #self.errorBox = QtWidgets.QGroupBox(self.threshold1Tab)
        self.errorBox=self.fillBox(self.threshold1Tab, "error threshold: threshold [ppm] = k/1000 * (m/z) +d",
                          ("k", "d", "tolerance for isotope peaks"),
                          {"k": (QtWidgets.QDoubleSpinBox(), "slope of error threshold function"),
                           "d": (QtWidgets.QDoubleSpinBox(), "intercept of ppm error"),
                           "errorTolerance": (QtWidgets.QDoubleSpinBox(),
                                              "tolerance for isotope peak search in ppm")})
        self.widgets["d"].setMinimum(-9.99)
        #self.qualityBox = QtWidgets.QGroupBox(self.threshold1Tab)
        self.qualityBox = self.fillBox(self.threshold1Tab, "Quality thresholds",
                     ("quality (deletion)","quality (highlighting)","score (highlightening)"),
                     {"shapeDel": (QtWidgets.QDoubleSpinBox(),
                       "ions which have a higher value are deleted"),
                      "shapeMarked": (QtWidgets.QDoubleSpinBox(),
                       "ions which have a higher value are highlighted"),
                      "scoreMarked": (QtWidgets.QDoubleSpinBox(),
                       "ions which have a higher value are highlighted")})
        #if yMax < yPos:
        #    yMax = yPos

        #self.noiseBox = QtWidgets.QGroupBox(self.threshold2Tab)
        self.noiseBox = self.fillBox(self.threshold2Tab, "noise calculation", ("window size","noise threshold tolerance"),
                            {"noiseWindowSize": (QtWidgets.QDoubleSpinBox(),
                                                 "window size for noise calculation"),
                             "thresholdFactor": (QtWidgets.QDoubleSpinBox(),
                                                 "set it lower to search for more isotope peaks")})
        #self.searchIntensityBox = QtWidgets.QGroupBox(self.threshold2Tab)
        self.searchIntensityBox = self.fillBox(self.threshold2Tab, "ion search and modelling",
                            ("charge tolerance", "outlier peak threshold"),
                            {"zTolerance": (QtWidgets.QDoubleSpinBox(),
                              "ions with charge states between the calculated charge +/- threshold are searched for"),
                             "outlierLimit": (QtWidgets.QDoubleSpinBox(),
                              "isotope peaks with higher values are not used for intensity modelling")})
        #self.remodellingBox = QtWidgets.QGroupBox(self.threshold2Tab)
        self.remodellingBox = self.fillBox(self.threshold2Tab, "modelling overlaps",
                            ("max. nr. of overlapping ions","threshold tolerance"),
                            {"manualDeletion": (QtWidgets.QSpinBox(),
                              "if overlap-pattern1 contains more ions, user is asked to manually delete ions"),
                             "overlapThreshold": (QtWidgets.QDoubleSpinBox(),
                              "ions which have a lower proportion in overlap pattern1 are deleted")})
        #if yMax < yPos:
        #    yMax = yPos

        #self.interestingIonsBox = QtWidgets.QGroupBox(self.outputTab)
        self.interestingIonsBox = self.fillInterestingIonsBox(self.outputTab)
        #configDialog.resize(375, yMax+100)
        self.verticalLayout.addWidget(self.buttonBox, 0, QtCore.Qt.AlignHCenter)
        self.backToLast()
        for fragItem in self.interestingIons:
            if fragItem.objectName() in (self.configHandler.get('interestingIons')):
                fragItem.setChecked(True)
        self.tabWidget.setCurrentIndex(3)
        #QtCore.QMetaObject.connectSlotsByName(configDialog)


    def accept(self):
        newConfigurations = self.makeDictToWrite()
        interestingIons = list()
        for fragItem in self.interestingIons:
            if fragItem.isChecked():
                interestingIons.append(fragItem.objectName())
        newConfigurations['interestingIons'] = interestingIons
        self.configHandler.write(newConfigurations)
        super(TD_configurationDialog, self).accept()


class IntactStartDialog(DialogWithTabs, StartDialog):
    def __init__(self, parent=None):
        super().__init__(parent,"Intact FragmentIon Search")
        self.configHandler = ConfigurationHandlerFactory.getIntactHandler()
        self.setupUi(self)

    def setupUi(self, startDialog):
        self.settingTab = self.createTab("Settings")
        settingLayout = QtWidgets.QFormLayout(self.settingTab)
        self.configTab = self.createTab("Configurations")
        configLayout = QtWidgets.QFormLayout(self.configTab)
        self.fill(self.settingTab, settingLayout,
                  ("Sequence Name", "Modification", "Spectral File", "Spray Mode", "Output"),
                  {"sequName": (QtWidgets.QLineEdit(), "Name of sequenceList"),
                   "modification": (QtWidgets.QLineEdit(), "Modification of precursor ion"),
                   "spectralData": (OpenFileWidget(self.settingTab, 1, join(path, 'Spectral_data', 'intact'), "Open File",
                                   "Plain Text Files (*txt);;All Files (*)"),
                                    "Name of the file with monoisotopic pattern (txt format)"),
                   "sprayMode": (self.createComboBox(self.settingTab, ("negative", "positive")), "Spray mode"),
                   "output": (QtWidgets.QLineEdit(self.settingTab),
                    "Name of the output txt file\ndefault: name of spectral pattern file + _out.txt")})
        if self.configHandler.getAll() != None:
            self.widgets['sprayMode'].setCurrentText(self._translate(self.objectName(), self.configHandler.get('sprayMode')))
        self.fill(self.configTab,configLayout,
                  ("min. m/z", "max. m/z", "max. raw error", "slope (k) of error", "intercept (d) of error"),
                  {"minMz": (QtWidgets.QSpinBox(), "m/z where search starts"),
                   "maxMz": (QtWidgets.QSpinBox(), "m/z where search ends"),
                   "errorLimitCalib": (QtWidgets.QSpinBox(), "max. ppm error in uncalbratied spectrum"),
                   "k": (QtWidgets.QDoubleSpinBox(),
                         "max. ppm error slope in calbratied spectrum (ppm = k/1000 + d)"),
                   "d": (QtWidgets.QDoubleSpinBox(),
                         "max. ppm error intercept in calbratied spectrum (ppm = k/1000 + d)")})
        #xMax, yMax = self.createWidgets(configWidgets, 200, 80)
        self.widgets['minMz'].setMaximum(9999)
        self.widgets['maxMz'].setMaximum(9999)
        self.widgets["d"].setMinimum(-9.99)
        self.backToLast()

        '''self.createLabels(("Sequence Name", "Modification", "Spectral File", "Spray Mode", "Output"),
                          self.settingTab, 10, 150)
        settingWidgets = ((QtWidgets.QLineEdit(self.settingTab), "sequName", "Name of sequenceList"),
                   (QtWidgets.QLineEdit(self.settingTab), "modification","Modification of precursor ion"),
                   (OpenFileWidget(self.settingTab,linewidth, 0, 1, join(path, 'Spectral_data','intact'),  "Open File",
                               "Plain Text Files (*txt);;All Files (*)"), "spectralData",
                        "Name of the file with monoisotopic pattern (txt format)"),
                   (self.createComboBox(self.settingTab,("negative","positive")), "sprayMode", "Spray mode"),
                   (QtWidgets.QLineEdit(self.settingTab), "output",
                        "Name of the output txt file\ndefault: name of spectral pattern file + _out.txt"))
        xPos, yPos = self.createWidgets(settingWidgets,120,linewidth)
        if yMax<yPos:
            yMax=yPos'''

        #self.defaultButton = self.makeDefaultButton(self)

        #self.defaultButton.setGeometry(QtCore.QRect(30, yMax + 56, 110, 32))
        self.verticalLayout.addWidget(self.makeButtonWidget(self), 0, QtCore.Qt.AlignRight)
        #startDialog.resize(340, yMax+100)
        #QtCore.QMetaObject.connectSlotsByName(startDialog)


    def makeButtonWidget(self, parent):
        widget = QtWidgets.QWidget(parent)
        horizontLayout = QtWidgets.QHBoxLayout(widget)
        self.makeButtonBox(widget)
        self.defaultButton = self.makeDefaultButton(widget)
        horizontLayout.addWidget(self.defaultButton)
        horizontLayout.addSpacing(50)
        horizontLayout.addWidget(self.buttonBox)
        return widget

    def accept(self):
        newSettings = self.getNewSettings() #self.makeDictToWrite()
        """if (newSettings['spectralData'][-4:] != '.txt') and (newSettings['spectralData'][-4:] != '.csv'):
            newSettings['spectralData'] += '.txt'
        self.checkValues(newSettings)"""
        self.configHandler.write(newSettings)
        super(IntactStartDialog, self).accept()


    def checkValues(self, configs, *args):
        return super(IntactStartDialog, self).checkValues(configs, 'intact')


