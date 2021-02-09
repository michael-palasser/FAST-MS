import traceback

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QDialog, QMessageBox, QFileDialog
from os.path import join, isfile

from src import path
from src.Exceptions import UnvalidInputException
from src.repositories.ConfigurationHandler import ConfigurationHandlerFactory
from src.Services import FragmentIonService, ModificationService, SequenceService
from src.views.StartDialogs import OpenFileWidget

dataPath = join(path, 'src', 'data')

class AbstractDialog(QDialog):
    def __init__(self, dialogName, title, lineSpacing, parent):
        super().__init__(parent)
        self.setObjectName(dialogName)
        self.lineSpacing = lineSpacing
        self.widgets = dict()
        self.sizePolicy = self.setNewSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self._translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(self._translate(dialogName, title))
        self.buttonBox = QtWidgets.QDialogButtonBox(self)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.newSettings = None
        self.move(300,100)
        self.canceled = False

    @staticmethod
    def setNewSizePolicy(horizontal, vertical):
        sizePolicy = QtWidgets.QSizePolicy(horizontal, vertical)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        return sizePolicy

    def createLabels(self, labelNames, box, xPos, lineWidth):
        labels = []
        yPos = 30
        #print(type(labelNames),type(box),type(xPos),type(lineWidth))
        for labelname in labelNames:
            label = QtWidgets.QLabel(box)
            label.setGeometry(QtCore.QRect(xPos,yPos,lineWidth,16))
            _translate = QtCore.QCoreApplication.translate
            label.setText(_translate(self.objectName(), labelname))
            labels.append(label)
            yPos += self.lineSpacing
        return labels


    def createWidgets(self, widgetTuples, xPos, lineWidth):
        """

        :param widgetTuples: (widget,name,toolTip)
        :param xPos:
        :param lineWidth:
        :return:
        """
        yPos = 30
        for widgetTuple in widgetTuples:
            widget = widgetTuple[0]
            if isinstance(widget, QtWidgets.QSpinBox) or isinstance(widget, QtWidgets.QDoubleSpinBox):
                widget.setGeometry(QtCore.QRect(xPos, yPos-1, lineWidth, 24))
            elif isinstance(widget, QtWidgets.QLineEdit):
                widget.setGeometry(QtCore.QRect(xPos, yPos, lineWidth, 21))
            elif isinstance(widget, QtWidgets.QComboBox):
                widget.setGeometry(QtCore.QRect(xPos - 3, yPos, lineWidth + 6, 26))
            elif isinstance(widget, OpenFileWidget):
                widget.setGeometry(QtCore.QRect(xPos, yPos-5, lineWidth + 20, 36))
            else:
                raise Exception('Unknown type of widget')
            widget.setObjectName(widgetTuple[1])
            widget.setToolTip(self._translate(self.objectName(), widgetTuple[2]))
            self.widgets[widgetTuple[1]] = widget
            yPos += self.lineSpacing
        return xPos+lineWidth, yPos


    def createComboBox(self, box, options):
        comboBox = QtWidgets.QComboBox(box)
        for i, option in enumerate(options):
            comboBox.addItem("")
            comboBox.setItemText(i, self._translate(self.objectName(), option))
        return comboBox

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

    def reshape(self, xPos, yPos):
        self.resize(xPos+25, yPos+70)
        QtCore.QMetaObject.connectSlotsByName(self)


class StartDialog(AbstractDialog):
    """def startProgram(self, mainMethod):
        self.makeDictToWrite()
        #try:
        mainMethod()"""
        #    super(StartDialog, self).accept()
        #except:
        #    traceback.print_exc()
         #   QMessageBox.warning(self, "Problem occured", traceback.format_exc(), QMessageBox.Ok)

    def makeDefaultButton(self):
        defaultButton = QtWidgets.QPushButton(self)
        self.sizePolicy.setHeightForWidth(defaultButton.sizePolicy().hasHeightForWidth())
        defaultButton.setSizePolicy(self.sizePolicy)
        defaultButton.setMinimumSize(QtCore.QSize(113, 0))
        defaultButton.clicked.connect(self.backToLast)
        defaultButton.setText(self._translate(self.objectName(), "last settings"))
        return defaultButton

    def getNewSettings(self):
        newSettings = self.makeDictToWrite()
        if (newSettings['spectralData'][-4:] != '.txt') and (newSettings['spectralData'][-4:] != '.csv') and (newSettings['spectralData']!=""):
            newSettings['spectralData'] += '.txt'
        try:
            newSettings = self.checkValues(newSettings)
        except UnvalidInputException:
            traceback.print_exc()
            QMessageBox.warning(self, "Problem occured", traceback.format_exc(), QMessageBox.Ok)
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
        super().__init__("startDialog","Settings", 30, parent)
        self.configHandler = ConfigurationHandlerFactory.getTD_SettingHandler()
        self.setupUi(self)

    def setupUi(self, startDialog):
        self.createLabels(("Sequence Name:", "Charge:", "Fragmentation:", "Modifications:", "Nr. of Modifications:",
                           "Spectral Data:", "Noise Threshold (x10^6):", "Fragment Library:"),#, "Output"),
                          startDialog, 30, 160)
        fragPatterns = FragmentIonService().getAllPatternNames()
        modPatterns = ModificationService().getAllPatternNames()
        sequences = SequenceService().getAllSequenceNames()
        linewidth = 200
        widgets = ((self.createComboBox(startDialog,sequences), "sequName", "Name of the sequence"),
               (QtWidgets.QSpinBox(startDialog), "charge","Charge of the precursor ion"),
               (self.createComboBox(startDialog,fragPatterns), "fragmentation", "Name of the fragmentation - pattern"),
               (self.createComboBox(startDialog,modPatterns), "modifications", "Name of the modification/ligand - pattern"),
               (QtWidgets.QSpinBox(startDialog), "nrMod", "How often is the precursor ion modified?"),
               (OpenFileWidget(self,linewidth, 0, 2, join(path, 'Spectral_data','top-down'),  "Open File",
                               "Plain Text Files (*txt);;Comma Separated Values (*csv);;All Files (*)"),
                "spectralData","Name of the file with spectral peaks (txt or csv format)\n"
                                     "If no file is stated, the program will just calculate the fragment library"),
               (QtWidgets.QDoubleSpinBox(startDialog), 'noiseLimit', "Minimal noise level"),
               (QtWidgets.QLineEdit(startDialog), "fragLib", "Name of csv file in the folder 'Fragment_lists' "
                     "containing the isotope patterns of the fragments\n"
                     "If no file is stated, the program will search for the corresponing file or create a new one"))
               #(QtWidgets.QLineEdit(startDialog), "output",
                    #"Name of the output Excel file\ndefault: name of spectral pattern file + _out.xlsx"))
        xPos, yPos = self.createWidgets(widgets,200,linewidth)
        self.widgets['charge'].setMinimum(-99)
        self.buttonBox.setGeometry(QtCore.QRect(210, yPos+20, 164, 32))
        #self.widgets['charge'].setValue(2)
        if self.configHandler.getAll() != None:
            try:
                self.widgets["fragmentation"].setCurrentText(self.configHandler.get('fragmentation'))
                self.widgets["modifications"].setCurrentText(self.configHandler.get('modifications'))
                self.widgets["nrMod"].setValue(self.configHandler.get('nrMod'))
            except KeyError:
                traceback.print_exc()
        self.defaultButton = self.makeDefaultButton()
        self.defaultButton.setGeometry(QtCore.QRect(40, yPos + 20, 113, 32))

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
    def __init__(self,dialogName, title, lineSpacing, parent=None):
        super().__init__(dialogName, title, lineSpacing, parent)
        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        #self.verticalLayout.setObjectName("verticalLayout")
        self.tabWidget = QtWidgets.QTabWidget(self)
        self.tabWidget.setEnabled(True)
        tabSizePolicy = self.setNewSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        tabSizePolicy.setHeightForWidth(self.tabWidget.sizePolicy().hasHeightForWidth())
        self.tabWidget.setSizePolicy(tabSizePolicy)
        self.verticalLayout.addWidget(self.tabWidget)

        self.sizePolicy.setHeightForWidth(self.buttonBox.sizePolicy().hasHeightForWidth())
        self.buttonBox.setSizePolicy(self.sizePolicy)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)


    def createTab(self,name):
        tab = QtWidgets.QWidget()
        self.tabWidget.addTab(tab, "")
        self.tabWidget.setTabText(self.tabWidget.indexOf(tab), self._translate(self.objectName(), name))
        return tab



class TD_configurationDialog(DialogWithTabs):
    def __init__(self, parent=None):
        super().__init__("configDialog", "Configurations", 30, parent)
        self.configHandler = ConfigurationHandlerFactory.getTD_ConfigHandler()
        self.interestingIons = list()
        self.tabs = dict()
        self.setupUi(self)

    def fillBox(self, box, title, yPos, labels, widgets):
        height = (len(labels)+1)*self.lineSpacing
        box.setTitle(self._translate(self.objectName(), title))
        box.setGeometry(QtCore.QRect(5, yPos, 320, height))
        box.setAutoFillBackground(False)
        self.createLabels(labels, box, 10, 200)
        self.createWidgets(widgets,240,70)
        return yPos+height

    def fillInterestingIonsBox(self):
        self.interestingIonsBox.setGeometry(QtCore.QRect(5, 10, 320, 90))
        self.interestingIonsBox.setTitle(self._translate("configDialog", "interesting ions"))
        self.interestingIonsBox.setToolTip(self._translate("configDialog",
                                                           "tick fragment types which should be more deeply analysed"))
        count = 0
        for key in ('a', 'b', 'c', 'd', 'w', 'x', 'y', 'z'):
            checkbox = QtWidgets.QCheckBox(self.interestingIonsBox)
            if count < 4:
                checkbox.setGeometry(QtCore.QRect(10+int(count/2)*70, 30+(count%2)*30 , 50, 20))
            else:
                checkbox.setGeometry(QtCore.QRect(60+int(count/2)*70, 30+(count%2)*30 , 50, 20))
            checkbox.setText(self._translate("configDialog", key))
            checkbox.setObjectName(key)
            self.interestingIons.append(checkbox)
            count +=1
        return 100+10


    def setupUi(self, configDialog):
        configDialog.move(200,100)
        self.spectrumTab = self.createTab("spectrum")
        self.threshold1Tab = self.createTab("thresholds 1")
        self.threshold2Tab = self.createTab("thresholds 2")
        self.outputTab = self.createTab("analysis/output")

        self.mzBox = QtWidgets.QGroupBox(self.spectrumTab)
        yPos = self.fillBox(self.mzBox, "m/z area containing peaks", 10,
                     ("min. m/z", "min. max. m/z", "tolerance", "window size"),
                     ((QtWidgets.QSpinBox(self.mzBox),"lowerBound", "configDialog",
                        "lower m/z bound (just peaks with higher m/z are examined)"),
                       (QtWidgets.QSpinBox(self.mzBox), "minUpperBound","minimal upper m/z bound"),
                       (QtWidgets.QSpinBox(self.mzBox),"upperBoundTolerance",
                        "value is added to calculated upper m/z-bound for final value"),
                       (QtWidgets.QDoubleSpinBox(self.mzBox),"upperBoundWindowSize",
                        "window size for noise calculation to find upper m/z bound")))
        self.widgets['lowerBound'].setMaximum(9999)
        self.widgets['minUpperBound'].setMaximum(9999)
        self.widgets['upperBoundTolerance'].setMaximum(999)
        yMax = yPos

        self.errorBox = QtWidgets.QGroupBox(self.threshold1Tab)
        yPos=self.fillBox(self.errorBox, "error threshold: threshold [ppm] = k/1000 * (m/z) +d", 10,
                     ("k", "d", "tolerance for isotope peaks"),
                     ((QtWidgets.QDoubleSpinBox(self.errorBox), "k", "slope of error threshold function"),
                        (QtWidgets.QDoubleSpinBox(self.errorBox), "d", "intercept of ppm error"),
                        (QtWidgets.QDoubleSpinBox(self.errorBox), "errorTolerance",
                         "tolerance for isotope peak search in ppm")))
        self.widgets["d"].setMinimum(-9.99)
        self.qualityBox = QtWidgets.QGroupBox(self.threshold1Tab)
        self.fillBox(self.qualityBox, "Quality thresholds",yPos+10,
                     ("quality (deletion)","quality (highlighting)","score (highlightening)"),
                     ((QtWidgets.QDoubleSpinBox(self.qualityBox),"shapeDel",
                       "ions which have a higher value are deleted"),
                      (QtWidgets.QDoubleSpinBox(self.qualityBox),"shapeMarked",
                       "ions which have a higher value are highlighted"),
                      (QtWidgets.QDoubleSpinBox(self.qualityBox), "scoreMarked",
                       "ions which have a higher value are highlighted")))
        if yMax < yPos:
            yMax = yPos

        self.noiseBox = QtWidgets.QGroupBox(self.threshold2Tab)
        yPos = self.fillBox(self.noiseBox, "noise calculation", 10,
                            ("window size","noise threshold tolerance"),
                            ((QtWidgets.QDoubleSpinBox(self.noiseBox),"noiseWindowSize",
                              "window size for noise calculation"),
                             (QtWidgets.QDoubleSpinBox(self.noiseBox), "thresholdFactor",
                               "set it lower to search for more isotope peaks"),))
        self.searchIntensityBox = QtWidgets.QGroupBox(self.threshold2Tab)
        yPos = self.fillBox(self.searchIntensityBox, "ion search and modelling", yPos+10,
                            ("charge tolerance", "outlier peak threshold"),
                            ((QtWidgets.QDoubleSpinBox(self.searchIntensityBox),"zTolerance",
                              "ions with charge states between the calculated charge +/- threshold are searched for"),
                             (QtWidgets.QDoubleSpinBox(self.searchIntensityBox),"outlierLimit",
                              "isotope peaks with higher values are not used for intensity modelling")))
        self.remodellingBox = QtWidgets.QGroupBox(self.threshold2Tab)
        yPos = self.fillBox(self.remodellingBox, "modelling overlaps", yPos+10,
                            ("max. nr. of overlapping ions","threshold tolerance"),
                            ((QtWidgets.QSpinBox(self.remodellingBox), "manualDeletion",
                              "if overlap-pattern1 contains more ions, user is asked to manually delete ions"),
                             (QtWidgets.QDoubleSpinBox(self.remodellingBox),"overlapThreshold",
                              "ions which have a lower proportion in overlap pattern1 are deleted")))
        if yMax < yPos:
            yMax = yPos

        self.interestingIonsBox = QtWidgets.QGroupBox(self.outputTab)
        self.fillInterestingIonsBox()
        configDialog.resize(375, yMax+100)
        self.verticalLayout.addWidget(self.buttonBox, 0, QtCore.Qt.AlignHCenter)
        self.backToLast()
        for fragItem in self.interestingIons:
            if fragItem.objectName() in (self.configHandler.get('interestingIons')):
                fragItem.setChecked(True)
        self.tabWidget.setCurrentIndex(3)
        QtCore.QMetaObject.connectSlotsByName(configDialog)


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
        super().__init__("intactStartDialog","Intact FragmentIon Search", 30, parent)
        self.configHandler = ConfigurationHandlerFactory.getIntactHandler()
        self.setupUi(self)

    def setupUi(self, startDialog):
        self.settingTab = self.createTab("Settings")
        self.configTab = self.createTab("Configurations")

        self.createLabels(("min. m/z", "max. m/z", "max. raw error", "slope (k) of error", "intercept (d) of error"),
                          self.configTab, 10, 200)
        configWidgets = ((QtWidgets.QSpinBox(self.configTab), "minMz", "m/z where search starts"),
                         (QtWidgets.QSpinBox(self.configTab), "maxMz", "m/z where search ends"),
                         (QtWidgets.QSpinBox(self.configTab), "errorLimitCalib",
                          "max. ppm error in uncalbratied spectrum"),
                         (QtWidgets.QDoubleSpinBox(self.configTab), "k",
                          "max. ppm error slope in calbratied spectrum (ppm = k/1000 + d)"),
                         (QtWidgets.QDoubleSpinBox(self.configTab), "d",
                          "max. ppm error intercept in calbratied spectrum (ppm = k/1000 + d)"))
        xMax, yMax = self.createWidgets(configWidgets, 200, 80)
        self.widgets['minMz'].setMaximum(9999)
        self.widgets['maxMz'].setMaximum(9999)
        self.widgets["d"].setMinimum(-9.99)
        self.backToLast()
        linewidth = 160
        self.createLabels(("Sequence Name", "Modification", "Spectral File", "Spray Mode", "Output"),
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
            yMax=yPos

        self.defaultButton = self.makeDefaultButton()
        if self.configHandler.getAll() != None:
            self.widgets['sprayMode'].setCurrentText(self._translate("startDialog", self.configHandler.get('sprayMode')))
        self.defaultButton.setGeometry(QtCore.QRect(30, yMax + 56, 110, 32))
        self.verticalLayout.addWidget(self.buttonBox, 0, QtCore.Qt.AlignRight)
        startDialog.resize(340, yMax+100)
        QtCore.QMetaObject.connectSlotsByName(startDialog)


    def accept(self):
        newSettings = self.getNewSettings() #self.makeDictToWrite()
        """if (newSettings['spectralData'][-4:] != '.txt') and (newSettings['spectralData'][-4:] != '.csv'):
            newSettings['spectralData'] += '.txt'
        self.checkValues(newSettings)"""
        self.configHandler.write(super(IntactStartDialog, self).accept())


    def checkValues(self, configs, *args):
        return super(IntactStartDialog, self).checkValues(configs, 'intact')


