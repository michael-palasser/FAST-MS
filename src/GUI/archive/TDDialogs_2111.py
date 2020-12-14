from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QDialog
from src import path
from src.ConfigurationHandler import ConfigHandler
from src.FragmentHunter.Main import run


class AbstractDialog(QDialog):
    def __init__(self, dialogName, lineSpacing, parent=None):
        super().__init__(parent)
        self.dialogName = dialogName
        self.lineSpacing = lineSpacing
        self.widgets = dict()
        self.sizePolicy = self.setNewSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self._translate = QtCore.QCoreApplication.translate

    @staticmethod
    def setNewSizePolicy(horizontal, vertical):
        sizePolicy = QtWidgets.QSizePolicy(horizontal, vertical)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        return sizePolicy

    """def createLabels(self, box, labelNames):
        labels = []
        row = 0
        for labelname in labelNames:
            label = QtWidgets.QLabel(box)
            self.gridLayout.addWidget(label, row, 0, 1, 1)
            _translate = QtCore.QCoreApplication.translate
            label.setText(_translate(self.dialogName, labelname))
            labels.append(label)
            row +=1
        return labels"""

    def createLabels(self, box, labelNames, xPos, lineWidth):
        labels = []
        yPos = 10
        for labelname in labelNames:
            label = QtWidgets.QLabel(box)
            label.setGeometry(QtCore.QRect(xPos,yPos,lineWidth,16))
            _translate = QtCore.QCoreApplication.translate
            label.setText(_translate(self.dialogName, labelname))
            labels.append(label)
            yPos += self.lineSpacing
        return labels


    """self.label_23 = QtWidgets.QLabel(self.mzBox)
    self.label_23.setGeometry(QtCore.QRect(10, 30, 60, 16))
    self.label_23.setObjectName("label_23")"""

    def createWidget(self, widget, row, name, toolTip):
        self.gridLayout.addWidget(widget, row, 1, 1, 1)
        #widget.setObjectName(name)
        widget.setToolTip(self._translate(self.dialogName, toolTip))
        self.widgets[name] = widget
        return widget


    def createComboBox(self, options):
        comboBox = QtWidgets.QComboBox(self.layoutWidget)
        pos = 0
        for option in options:
            comboBox.addItem("")
            comboBox.setItemText(pos, self._translate(self.dialogName, option))
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

    def reject(self):
        self.done(1)

class TDStartDialog(AbstractDialog):
    def __init__(self, parent=None):
        super().__init__("startDialog", parent)
        self.configHandler = ConfigHandler(path+"src/FragmentHunter/settings.json")
        self.setupUi(self)

    def setupUi(self, startDialog):
        startDialog.setObjectName(self.dialogName)
        startDialog.resize(412, 307)
        self.buttonBox = QtWidgets.QDialogButtonBox(startDialog)
        self.buttonBox.setGeometry(QtCore.QRect(210, 260, 164, 32))
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)

        self.layoutWidget = QtWidgets.QWidget(startDialog)
        self.layoutWidget.setGeometry(QtCore.QRect(30, 20, 351, 216))
        self.gridLayout = QtWidgets.QGridLayout(self.layoutWidget)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)

        self.createLabels(self.layoutWidget, ("sequence name", "charge", "modification", "spectral data",
                                              "noise threshold (x10^6)", "spray mode", "dissociation"))
        self.createWidget(QtWidgets.QLineEdit(self.layoutWidget),0, "sequName",
                                          "name of sequence")
        self.createWidget(QtWidgets.QSpinBox(self.layoutWidget), 1, "charge",
                                        "charge of precursor ion")
        self.widgets['charge'].setValue(2)
        self.createWidget(QtWidgets.QLineEdit(self.layoutWidget), 2, "modification","modification of precursor ion")
        self.createWidget(QtWidgets.QLineEdit(self.layoutWidget), 3, "spectralData",
                                              "name of the file with spectral peaks (txt or csv format)")
        self.createWidget(QtWidgets.QDoubleSpinBox(self.layoutWidget), 4, 'noiseLimit', "minimal noise level")
        self.createWidget(self.createComboBox(("negative","positive")), 5, "sprayMode", "spray mode")
        self.createWidget(self.createComboBox(("CAD","ECD","EDD")), 6, "dissociation", "dissociation mode")
        self.widgets["dissociation"].setCurrentText(self.configHandler.get('dissociation'))
        self.defaultButton = QtWidgets.QPushButton(startDialog)
        self.defaultButton.setGeometry(QtCore.QRect(40, 260, 113, 32))


        self.sizePolicy.setHeightForWidth(self.defaultButton.sizePolicy().hasHeightForWidth())
        self.defaultButton.setSizePolicy(self.sizePolicy)
        self.defaultButton.setMinimumSize(QtCore.QSize(113, 0))
        #self.defaultButton.setObjectName("defaultButton")
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.defaultButton.clicked.connect(self.backToLast)
        self.retranslateUi(startDialog)
        QtCore.QMetaObject.connectSlotsByName(startDialog)


    def retranslateUi(self, startDialog):
        _translate = QtCore.QCoreApplication.translate
        startDialog.setWindowTitle(_translate("startDialog", "Dialog"))
        self.widgets['sprayMode'].setCurrentText(_translate("startDialog", self.configHandler.get('sprayMode')))
        self.defaultButton.setText(_translate("startDialog", "last settings"))

    def accept(self):
        newSettings = dict()
        for name, item in self.widgets.items():
            newSettings[name] = self.getValueOfWidget(item)
        newSettings['noiseLimit']*=10**6
        self.configHandler.write(newSettings)
        run()


    def backToLast(self):
        for name, item in self.widgets.items():
            if name == 'noiseLimit':
                self.setValueOfWidget(item, self.configHandler.get(name) / 10**6)
            else:
                self.setValueOfWidget(item, self.configHandler.get(name))



class TD_configurationDialog(AbstractDialog):

    def __init__(self, parent=None):
        super().__init__("configDialog", parent)
        self.configHandler = ConfigHandler(path+"src/FragmentHunter/configurations.json")
        self.setupUi(self)

    def setupUi(self, configDialog):
        #configDialog.setObjectName(self.dialogName)
        configDialog.resize(383, 389)
        self.verticalLayout = QtWidgets.QVBoxLayout(configDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.tabWidget = QtWidgets.QTabWidget(configDialog)
        self.tabWidget.setEnabled(True)
        tabSizePolicy = self.setNewSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        tabSizePolicy.setHeightForWidth(self.tabWidget.sizePolicy().hasHeightForWidth())
        self.tabWidget.setSizePolicy(tabSizePolicy)
        #self.tabWidget.setObjectName("tabWidget")
        self.spectrumTab = QtWidgets.QWidget()
        #self.spectrumTab.setObjectName("tab_2")
        self.mzBox = QtWidgets.QGroupBox(self.spectrumTab)
        self.mzBox.setGeometry(QtCore.QRect(10, 10, 330, 150))
        self.mzBox.setAutoFillBackground(False)
        #self.mzBox.setObjectName("mzBox")

        self.label_23 = QtWidgets.QLabel(self.mzBox)
        self.label_23.setGeometry(QtCore.QRect(10, 30, 60, 16))
        self.label_23.setObjectName("label_23")

        self.label_24 = QtWidgets.QLabel(self.mzBox)
        self.label_24.setGeometry(QtCore.QRect(10, 60, 171, 16))
        self.label_24.setObjectName("label_24")
        self.label_25 = QtWidgets.QLabel(self.mzBox)
        self.label_25.setGeometry(QtCore.QRect(10, 120, 191, 16))
        self.label_25.setObjectName("label_25")
        self.label_26 = QtWidgets.QLabel(self.mzBox)
        self.label_26.setGeometry(QtCore.QRect(10, 90, 161, 16))
        self.label_26.setObjectName("label_26")
        self.upperBoundWindowSize = QtWidgets.QDoubleSpinBox(self.mzBox)
        self.upperBoundWindowSize.setGeometry(QtCore.QRect(230, 116, 80, 24))
        self.upperBoundWindowSize.setObjectName("upperBoundWindowSize")
        self.lowerBound = QtWidgets.QSpinBox(self.mzBox)
        self.lowerBound.setGeometry(QtCore.QRect(230, 26, 80, 24))
        self.lowerBound.setMaximum(9999)
        self.lowerBound.setObjectName("lowerBound")
        self.minUpperBound = QtWidgets.QSpinBox(self.mzBox)
        self.minUpperBound.setGeometry(QtCore.QRect(230, 56, 80, 24))
        self.minUpperBound.setMaximum(9999)
        self.minUpperBound.setObjectName("minUpperBound")
        self.upperBoundTolerance = QtWidgets.QSpinBox(self.mzBox)
        self.upperBoundTolerance.setGeometry(QtCore.QRect(230, 86, 80, 24))
        self.upperBoundTolerance.setMaximum(999)
        self.upperBoundTolerance.setObjectName("upperBoundTolerance")
        self.tabWidget.addTab(self.spectrumTab, "")
        self.threshold1Tab = QtWidgets.QWidget()
        #self.threshold1Tab.setObjectName("tab")
        self.errorBox = QtWidgets.QGroupBox(self.threshold1Tab)
        self.errorBox.setGeometry(QtCore.QRect(10, 10, 330, 120))
        self.errorBox.setAutoFillBackground(False)
        #self.errorBox.setObjectName("errorBox")
        self.label_16 = QtWidgets.QLabel(self.errorBox)
        self.label_16.setGeometry(QtCore.QRect(10, 30, 60, 16))
        self.label_16.setObjectName("label_16")
        self.label_17 = QtWidgets.QLabel(self.errorBox)
        self.label_17.setGeometry(QtCore.QRect(10, 60, 60, 16))
        self.label_17.setObjectName("label_17")
        self.k = QtWidgets.QDoubleSpinBox(self.errorBox)
        self.k.setGeometry(QtCore.QRect(240, 26, 70, 24))
        self.k.setDecimals(2)
        self.k.setObjectName("k")
        self.d = QtWidgets.QDoubleSpinBox(self.errorBox)
        self.d.setGeometry(QtCore.QRect(240, 56, 70, 24))
        self.d.setMinimum(-9.99)
        self.d.setObjectName("d")
        self.errorTolerance = QtWidgets.QDoubleSpinBox(self.errorBox)
        self.errorTolerance.setGeometry(QtCore.QRect(240, 86, 70, 24))
        self.errorTolerance.setObjectName("errorTolerance")
        self.label_19 = QtWidgets.QLabel(self.errorBox)
        self.label_19.setGeometry(QtCore.QRect(10, 90, 171, 16))
        self.label_19.setObjectName("label_19")
        self.qualityBox = QtWidgets.QGroupBox(self.threshold1Tab)
        self.qualityBox.setGeometry(QtCore.QRect(10, 140, 330, 120))
        #self.qualityBox.setObjectName("qualityBox")
        self.label_20 = QtWidgets.QLabel(self.qualityBox)
        self.label_20.setGeometry(QtCore.QRect(10, 64, 141, 16))
        self.label_20.setObjectName("label_20")
        self.label_21 = QtWidgets.QLabel(self.qualityBox)
        self.label_21.setGeometry(QtCore.QRect(10, 94, 151, 16))
        self.label_21.setObjectName("label_21")
        self.shapeDel = QtWidgets.QDoubleSpinBox(self.qualityBox)
        self.shapeDel.setGeometry(QtCore.QRect(240, 30, 70, 24))
        self.shapeDel.setObjectName("shapeDel")
        self.shapeMarked = QtWidgets.QDoubleSpinBox(self.qualityBox)
        self.shapeMarked.setGeometry(QtCore.QRect(240, 60, 70, 24))
        self.shapeMarked.setObjectName("shapeMarked")
        self.label_22 = QtWidgets.QLabel(self.qualityBox)
        self.label_22.setGeometry(QtCore.QRect(10, 34, 141, 16))
        self.label_22.setObjectName("label_22")
        self.scoreMarked = QtWidgets.QDoubleSpinBox(self.qualityBox)
        self.scoreMarked.setGeometry(QtCore.QRect(240, 90, 70, 24))
        self.scoreMarked.setObjectName("scoreMarked")
        self.tabWidget.addTab(self.threshold1Tab, "")
        self.threshold2Tab = QtWidgets.QWidget()
        self.threshold2Tab.setObjectName("tab_4")
        self.noiseBox = QtWidgets.QGroupBox(self.threshold2Tab)
        self.noiseBox.setGeometry(QtCore.QRect(10, 10, 330, 90))
        #self.noiseBox.setObjectName("noiseBox")
        self.label_29 = QtWidgets.QLabel(self.noiseBox)
        self.label_29.setGeometry(QtCore.QRect(10, 60, 171, 16))
        self.label_29.setObjectName("label_29")
        self.thresholdFactor = QtWidgets.QDoubleSpinBox(self.noiseBox)
        self.thresholdFactor.setGeometry(QtCore.QRect(240, 56, 70, 24))
        self.thresholdFactor.setObjectName("thresholdFactor")
        self.label_37 = QtWidgets.QLabel(self.noiseBox)
        self.label_37.setGeometry(QtCore.QRect(10, 30, 140, 16))
        self.label_37.setObjectName("label_37")
        self.noiseWindowSize = QtWidgets.QDoubleSpinBox(self.noiseBox)
        self.noiseWindowSize.setGeometry(QtCore.QRect(240, 26, 70, 24))
        self.noiseWindowSize.setObjectName("noiseWindowSize")
        self.remodellingBox = QtWidgets.QGroupBox(self.threshold2Tab)
        self.remodellingBox.setGeometry(QtCore.QRect(10, 210, 330, 90))
        self.remodellingBox.setObjectName("remodellingBox")
        self.label_38 = QtWidgets.QLabel(self.remodellingBox)
        self.label_38.setGeometry(QtCore.QRect(10, 60, 141, 16))
        self.label_38.setObjectName("label_38")
        self.overlapThreshold = QtWidgets.QDoubleSpinBox(self.remodellingBox)
        self.overlapThreshold.setGeometry(QtCore.QRect(240, 56, 70, 24))
        self.overlapThreshold.setObjectName("overlapThreshold")
        self.label_39 = QtWidgets.QLabel(self.remodellingBox)
        self.label_39.setGeometry(QtCore.QRect(10, 30, 201, 16))
        self.label_39.setObjectName("label_39")
        self.manualDeletion = QtWidgets.QSpinBox(self.remodellingBox)
        self.manualDeletion.setGeometry(QtCore.QRect(240, 26, 70, 24))
        self.manualDeletion.setToolTip("")
        self.manualDeletion.setObjectName("manualDeletion")
        self.searchIntensityBox = QtWidgets.QGroupBox(self.threshold2Tab)
        self.searchIntensityBox.setGeometry(QtCore.QRect(10, 110, 330, 90))
        #self.searchIntensityBox.setObjectName("searchIntensityBox")
        self.outlierLimit = QtWidgets.QDoubleSpinBox(self.searchIntensityBox)
        self.outlierLimit.setGeometry(QtCore.QRect(240, 56, 70, 24))
        self.outlierLimit.setObjectName("outlierLimit")
        self.label_31 = QtWidgets.QLabel(self.searchIntensityBox)
        self.label_31.setGeometry(QtCore.QRect(10, 30, 141, 16))
        self.label_31.setObjectName("label_31")
        self.zTolerance = QtWidgets.QDoubleSpinBox(self.searchIntensityBox)
        self.zTolerance.setGeometry(QtCore.QRect(240, 26, 70, 24))
        self.zTolerance.setObjectName("zTolerance")
        self.label_32 = QtWidgets.QLabel(self.searchIntensityBox)
        self.label_32.setGeometry(QtCore.QRect(10, 60, 141, 16))
        self.label_32.setObjectName("label_32")
        self.tabWidget.addTab(self.threshold2Tab, "")
        self.outputTab = QtWidgets.QWidget()
        self.outputTab.setObjectName("tab_3")
        self.interestingIonsBox = QtWidgets.QGroupBox(self.outputTab)
        self.interestingIonsBox.setGeometry(QtCore.QRect(10, 10, 330, 90))
        #self.interestingIonsBox.setObjectName("interestingIonsBox")
        self.aFrag = QtWidgets.QCheckBox(self.interestingIonsBox)
        self.aFrag.setGeometry(QtCore.QRect(10, 30, 50, 20))
        self.aFrag.setObjectName("aFrag")
        self.bFrag = QtWidgets.QCheckBox(self.interestingIonsBox)
        self.bFrag.setGeometry(QtCore.QRect(10, 60, 50, 20))
        self.bFrag.setObjectName("bFrag")
        self.cFrag = QtWidgets.QCheckBox(self.interestingIonsBox)
        self.cFrag.setGeometry(QtCore.QRect(80, 30, 50, 20))
        self.cFrag.setObjectName("cFrag")
        self.dFrag = QtWidgets.QCheckBox(self.interestingIonsBox)
        self.dFrag.setGeometry(QtCore.QRect(80, 60, 50, 20))
        self.dFrag.setObjectName("dFrag")
        self.wFrag = QtWidgets.QCheckBox(self.interestingIonsBox)
        self.wFrag.setGeometry(QtCore.QRect(200, 30, 50, 20))
        self.wFrag.setChecked(False)
        self.wFrag.setTristate(False)
        self.wFrag.setObjectName("wFrag")
        self.xFrag = QtWidgets.QCheckBox(self.interestingIonsBox)
        self.xFrag.setGeometry(QtCore.QRect(200, 60, 50, 20))
        self.xFrag.setObjectName("xFrag")
        self.yFrag = QtWidgets.QCheckBox(self.interestingIonsBox)
        self.yFrag.setGeometry(QtCore.QRect(270, 30, 50, 20))
        self.yFrag.setObjectName("yFrag")
        self.zFrag = QtWidgets.QCheckBox(self.interestingIonsBox)
        self.zFrag.setGeometry(QtCore.QRect(270, 60, 50, 20))
        self.zFrag.setObjectName("zFrag")
        self.tabWidget.addTab(self.outputTab, "")
        self.verticalLayout.addWidget(self.tabWidget)
        self.buttonBox = QtWidgets.QDialogButtonBox(configDialog)
        self.sizePolicy.setHeightForWidth(self.buttonBox.sizePolicy().hasHeightForWidth())
        self.buttonBox.setSizePolicy(self.sizePolicy)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        #self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox, 0, QtCore.Qt.AlignHCenter)

        self.digitDict = {self.lowerBound:'lowerBound', self.minUpperBound:'minUpperBound', self.upperBoundTolerance:
                            'upperBoundTolerance', self.upperBoundWindowSize:'upperBoundWindowSize',
                          self.k:'k', self.d:'d', self.errorTolerance:'errorTolerance',
                          self.shapeDel:'shapeDel', self.shapeMarked:'shapeMarked', self.scoreMarked:'scoreMarked',
                          self.noiseWindowSize:'noiseWindowSize', self.thresholdFactor:'thresholdFactor',
                          self.zTolerance:'zTolerance', self.outlierLimit:'outlierLimit',
                          self.manualDeletion:'manualDeletion', self.overlapThreshold:'overlapThreshold'}
        self.fragmentDict = {self.aFrag:'a', self.bFrag:'b', self.cFrag:'c', self.dFrag:'d',
                             self.wFrag:'w', self.xFrag:'x', self.yFrag:'y', self.zFrag:'z'}

        for item,key in self.digitDict.items():
            item.setValue(self.configHandler.get(key))
        for item,fragString in self.fragmentDict.items():
            if fragString in (self.configHandler.get('interestingIons')):
                item.setChecked(True)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.retranslateUi(configDialog)
        self.tabWidget.setCurrentIndex(3)
        QtCore.QMetaObject.connectSlotsByName(configDialog)

    def retranslateUi(self, configDialog):
        _translate = QtCore.QCoreApplication.translate
        configDialog.setWindowTitle(_translate("configDialog", "Dialog"))
        self.mzBox.setTitle(_translate("configDialog", "m/z area containing peaks"))
        self.label_23.setText(_translate("configDialog", "min. m/z"))
        self.label_24.setText(_translate("configDialog", "min. max. m/z"))
        self.label_25.setText(_translate("configDialog", "window size"))
        self.label_26.setText(_translate("configDialog", "tolerance"))
        self.upperBoundWindowSize.setToolTip(_translate("configDialog", "window size for noise calculation to find upper m/z bound"))
        self.lowerBound.setToolTip(_translate("configDialog", "lower m/z bound (just peaks with higher m/z are examined) "))
        self.minUpperBound.setToolTip(_translate("configDialog", "minimal upper m/z bound"))
        self.upperBoundTolerance.setToolTip(_translate("configDialog", "value is added to calculated upper m/z-bound for final value"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.spectrumTab), _translate("configDialog", "spectrum"))
        self.errorBox.setTitle(_translate("configDialog", "error threshold: threshold [ppm] = k/1000 * (m/z) +d"))
        self.label_16.setToolTip(_translate("configDialog", "slope"))
        self.label_16.setText(_translate("configDialog", "k"))
        self.label_17.setToolTip(_translate("configDialog", "intercept"))
        self.label_17.setText(_translate("configDialog", "d"))
        self.k.setToolTip(_translate("configDialog", "slope of ppm error"))
        self.d.setToolTip(_translate("configDialog", "intercept of ppm error"))
        self.errorTolerance.setToolTip(_translate("configDialog", "tolerance for isotope peak search in ppm"))
        self.label_19.setText(_translate("configDialog", "tolerance for isotope peaks"))
        self.qualityBox.setTitle(_translate("configDialog", "Quality thresholds"))
        self.label_20.setText(_translate("configDialog", "quality (highlighting)"))
        self.label_21.setText(_translate("configDialog", "score (highlightening)"))
        self.shapeDel.setToolTip(_translate("configDialog", "ions which have a higher value are highlighted"))
        self.shapeMarked.setToolTip(_translate("configDialog", "ions which have a higher value are highlighted"))
        self.label_22.setText(_translate("configDialog", "quality (deletion)"))
        self.scoreMarked.setToolTip(_translate("configDialog", "ions which have a higher value are highlighted"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.threshold1Tab), _translate("configDialog", "thresholds 1"))
        self.noiseBox.setTitle(_translate("configDialog", "noise calculation"))
        self.label_29.setText(_translate("configDialog", "threshold tolerance"))
        self.thresholdFactor.setToolTip(_translate("configDialog", "set it lower to search for more isotope peaks"))
        self.label_37.setText(_translate("configDialog", "window size"))
        self.noiseWindowSize.setToolTip(_translate("configDialog", "window size for noise calculation"))
        self.remodellingBox.setTitle(_translate("configDialog", "modelling overlaps"))
        self.label_38.setText(_translate("configDialog", "threshold tolerance"))
        self.overlapThreshold.setToolTip(_translate("configDialog", "ions which have a lower proportion in overlap pattern1 are deleted"))
        self.label_39.setText(_translate("configDialog", "max. nr. of overlapping ions"))
        self.manualDeletion.setToolTip(_translate("configDialog", "if overlap-pattern1 contains more ions, user is asked to manually delete ions"))
        self.searchIntensityBox.setTitle(_translate("configDialog", "ion search and modelling"))
        self.outlierLimit.setToolTip(_translate("configDialog", "ions which have a higher value are highlighted"))
        self.label_31.setText(_translate("configDialog", "charge tolerance"))
        self.zTolerance.setToolTip(_translate("configDialog", "isotope peaks with higher values are not used for intensity modelling"))
        self.label_32.setText(_translate("configDialog", "outlier peak threshold"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.threshold2Tab), _translate("configDialog", "thresholds 2"))
        self.interestingIonsBox.setToolTip(_translate("configDialog", "tick fragment types which should be more deeply analysed"))
        self.interestingIonsBox.setToolTip(_translate("configDialog", "tick fragment types which should be more deeply analysed"))
        self.interestingIonsBox.setTitle(_translate("configDialog", "interesting ions"))
        self.aFrag.setText(_translate("configDialog", "a"))
        self.bFrag.setText(_translate("configDialog", "b"))
        self.cFrag.setText(_translate("configDialog", "c"))
        self.dFrag.setText(_translate("configDialog", "d"))
        self.wFrag.setText(_translate("configDialog", "w"))
        self.xFrag.setText(_translate("configDialog", "x"))
        self.yFrag.setText(_translate("configDialog", "y"))
        self.zFrag.setText(_translate("configDialog", "z"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.outputTab), _translate("configDialog", "analysis/output"))


    #ToDo
    def accept(self):
        newConfigurations = dict()
        interestingIons = list()
        for item,key in self.digitDict.items():
            newConfigurations[key] = item.value()
        for item, fragString in self.fragmentDict:
            if item.isChecked():
                interestingIons.append(fragString)
        newConfigurations['interestingIons'] = interestingIons
        self.configHandler.write(newConfigurations)
        self.done(0)

class ParameterBox(object):
    def __init__(self, box, dialog, lineSpacing):
        self.box = box
        self.dialog = dialog
        self.lineSpacing = lineSpacing
        #self.layoutWidget = QtWidgets.QWidget(self.dialog)
        #self.layoutWidget.setGeometry(geometry)
        #self.gridLayout = QtWidgets.QGridLayout(self.layoutWidget)
        #self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self._translate = QtCore.QCoreApplication.translate


    def fillBox(self, labels, widgets):
        self.createLabels(labels)

    def createLabels(self, labelNames, xPos, lineWidth):
        labels = []
        yPos = 10
        for labelname in labelNames:
            label = QtWidgets.QLabel(self.box)
            label.setGeometry(QtCore.QRect(xPos,yPos,lineWidth,16))
            #self.gridLayout.addWidget(label, row, 0, 1, 1)
            _translate = QtCore.QCoreApplication.translate
            label.setText(_translate(self.dialog.objectName(), labelname))
            labels.append(label)
            yPos += self.lineSpacing
        return labels

    def createWidget(self, widget, row, name, toolTip):
        self.gridLayout.addWidget(widget, row, 1, 1, 1)
        #widget.setObjectName(name)
        widget.setToolTip(self._translate(self.dialog.objectName(), toolTip))
        #widgets[name] = widget
        return widget

    def createComboBox(self, options):
        comboBox = QtWidgets.QComboBox(self.layoutWidget)
        pos = 0
        for option in options:
            comboBox.addItem("")
            comboBox.setItemText(pos, self._translate(self.dialog.objectName(), option))
            pos +=1
        return comboBox