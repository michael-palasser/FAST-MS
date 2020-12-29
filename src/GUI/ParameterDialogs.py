import traceback

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QDialog, QMessageBox
from src import path
from src.ConfigurationHandler import ConfigHandler
from src.FragmentHunter import Main
from src.Intact_Ion_Search import ESI_Main
from os.path import join

fragmentHunterRepPath = join(path, 'src', 'FragmentHunter', 'Repository')

class AbstractDialog(QDialog):
    def __init__(self, dialogName, title, lineSpacing, parent=None):
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
        self.move(300,100)

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
            else:
                raise Exception('Unknown type of widget')
            widget.setObjectName(widgetTuple[1])
            widget.setToolTip(self._translate(self.objectName(), widgetTuple[2]))
            self.widgets[widgetTuple[1]] = widget
            yPos += self.lineSpacing
        return xPos+lineWidth, yPos


    def createComboBox(self, box, options):
        comboBox = QtWidgets.QComboBox(box)
        pos = 0
        for option in options:
            comboBox.addItem("")
            comboBox.setItemText(pos, self._translate(self.objectName(), option))
            pos +=1
        return comboBox



    @staticmethod
    def getValueOfWidget(widget):
        if isinstance(widget, QtWidgets.QSpinBox) or isinstance(widget, QtWidgets.QDoubleSpinBox):
            return widget.value()
        elif isinstance(widget, QtWidgets.QLineEdit):
            return widget.text()
        elif isinstance(widget, QtWidgets.QComboBox):
            return widget.currentText()
        else:
            raise Exception('Unknown type of widget')

    @staticmethod
    def setValueOfWidget(widget, value):
        if isinstance(widget, QtWidgets.QSpinBox) or isinstance(widget, QtWidgets.QDoubleSpinBox):
            widget.setValue(value)
        elif isinstance(widget, QtWidgets.QLineEdit):
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
        self.done(0)

    def makeDictToWrite(self):
        newSettings = dict()
        for name, item in self.widgets.items():
            newSettings[name] = self.getValueOfWidget(item)
        return newSettings


    def accept(self):
        self.done(0)

    def reshape(self, xPos, yPos):
        self.resize(xPos+25, yPos+70)
        QtCore.QMetaObject.connectSlotsByName(self)


class StartDialog(AbstractDialog):
    def startProgram(self, mainMethod):
        self.makeDictToWrite()
        try:
            mainMethod()
            super(StartDialog, self).accept()
        except:
            traceback.print_exc()
            QMessageBox.warning(self, "Problem occured", traceback.format_exc(), QMessageBox.Ok)

    def makeDefaultButton(self):
        defaultButton = QtWidgets.QPushButton(self)
        self.sizePolicy.setHeightForWidth(defaultButton.sizePolicy().hasHeightForWidth())
        defaultButton.setSizePolicy(self.sizePolicy)
        defaultButton.setMinimumSize(QtCore.QSize(113, 0))
        defaultButton.clicked.connect(self.backToLast)
        defaultButton.setText(self._translate(self.objectName(), "last settings"))
        return defaultButton


class TDStartDialog(StartDialog):
    def __init__(self, parent=None):
        super().__init__("startDialog","Settings", 30, parent)
        self.configHandler = ConfigHandler(join(fragmentHunterRepPath, "settings.json"))
        self.setupUi(self)

    def setupUi(self, startDialog):
        self.createLabels(("sequence name", "charge", "modification", "spectral data", "noise threshold (x10^6)",
                           "spray mode", "dissociation", "output"),startDialog, 30, 150)
        widgets = ((QtWidgets.QLineEdit(startDialog), "sequName", "name of sequence"),
                   (QtWidgets.QSpinBox(startDialog), "charge","charge of precursor ion"),
                   (QtWidgets.QLineEdit(startDialog), "modification","modification of precursor ion"),
                   (QtWidgets.QLineEdit(startDialog), "spectralData","name of the file with spectral peaks (txt or csv format)"),
                   (QtWidgets.QDoubleSpinBox(startDialog), 'noiseLimit', "minimal noise level"),
                   (self.createComboBox(startDialog,("negative","positive")), "sprayMode", "spray mode"),
                   (self.createComboBox(startDialog,("CAD", "ECD", "EDD")), "dissociation", "dissociation mode"),
                   (QtWidgets.QLineEdit(startDialog), "output",
                        "name of the output Excel file\ndefault: name of spectral data file + _out.xlsx"))
        xPos, yPos = self.createWidgets(widgets,190,200)
        #startDialog.resize(412, 307)
        self.buttonBox.setGeometry(QtCore.QRect(210, yPos+20, 164, 32))
        self.widgets['charge'].setValue(2)
        if self.configHandler.getAll() != None:
            self.widgets["dissociation"].setCurrentText(self.configHandler.get('dissociation'))
            self.widgets['sprayMode'].setCurrentText(self._translate("startDialog", self.configHandler.get('sprayMode')))
        self.defaultButton = self.makeDefaultButton()
        self.defaultButton.setGeometry(QtCore.QRect(40, yPos + 20, 113, 32))




    def backToLast(self):
        super(TDStartDialog, self).backToLast()
        self.setValueOfWidget(self.widgets['noiseLimit'], self.configHandler.get('noiseLimit') / 10**6)

    def accept(self):
        newSettings = self.makeDictToWrite()
        newSettings['noiseLimit']*=10**6
        self.configHandler.write(newSettings)
        self.startProgram(Main.run)



class DialogWithTabs(AbstractDialog):
    def __init__(self,dialogName, title, lineSpacing, parent=None):
        super().__init__(dialogName, title, lineSpacing, parent)
        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setObjectName("verticalLayout")
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
        self.configHandler = ConfigHandler(join(fragmentHunterRepPath, "configurations.json"))
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


class ESI_StartDialog(DialogWithTabs, StartDialog):
    def __init__(self, parent=None):
        super().__init__("ESI_startDialog","Intact Ion Search", 30, parent)
        self.configHandler = ConfigHandler(join(path,"src","Intact_Ion_Search","Repository","configurations.json"))
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

        self.createLabels(("sequence name", "modification", "spectral data file",
                           "spray mode", "output"), self.settingTab, 10, 150)
        settingWidgets = ((QtWidgets.QLineEdit(self.settingTab), "sequName", "name of sequence"),
                   (QtWidgets.QLineEdit(self.settingTab), "modification","modification of precursor ion"),
                   (QtWidgets.QLineEdit(self.settingTab), "spectralData",
                        "name of the file with monoisotopic data (txt format)"),
                   (self.createComboBox(self.settingTab,("negative","positive")), "sprayMode", "spray mode"),
                   (QtWidgets.QLineEdit(self.settingTab), "output",
                        "name of the output txt file\ndefault: name of spectral data file + _out.txt"))
        xPos, yPos = self.createWidgets(settingWidgets,120,160)
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
        newSettings = self.makeDictToWrite()
        self.configHandler.write(newSettings)
        self.startProgram(ESI_Main.run)

