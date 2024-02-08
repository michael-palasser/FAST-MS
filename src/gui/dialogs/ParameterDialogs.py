from PyQt5 import QtCore, QtWidgets
from os.path import join

from src.resources import path
from src.gui.GUI_functions import shoot
from src.gui.dialogs.AbstractDialogs import DialogWithTabs
from src.repositories.ConfigurationHandler import ConfigurationHandlerFactory

dataPath = join(path, 'src', 'data')


class ConfigurationDialog(DialogWithTabs):
    '''
    Dialog for editing top-down search parameters/configurations
    '''
    def __init__(self, parent):
        super().__init__(parent, "Configurations")
        self._configHandler = ConfigurationHandlerFactory.getConfigHandler()
        self._interestingIons = list()
        self._addIons = list()
        self._tabs = dict()
        self._boxSizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.setupUi(self)
        self._verticalLayout.addWidget(self._buttonBox, 0, QtCore.Qt.AlignRight)
        shoot(self)


    def createTab(self,name):
        tab = super(ConfigurationDialog, self).createTab(name)
        verticalLayout = QtWidgets.QVBoxLayout(tab)
        tab.setLayout(verticalLayout)
        return tab

    def fillBox(self, parent, title, labels, widgets):
        '''
        Constructs a QGroupBox and fills it with QLabels and QWidgets
        :param parent:
        :param (str) title:
        :param (list[str] | tuple[str]) labels:
        :param (dict[str, tuple[QWidget, str]]) widgets: dict of name (widget, tooltip)
        :return: (QGroupBox) box
        '''
        #height = (len(labels)+1)*self.lineSpacing
        box = QtWidgets.QGroupBox(parent)
        box.setSizePolicy(self._boxSizePolicy)
        box.setTitle(self._translate(self.objectName(), title))
        box.setAutoFillBackground(False)
        formLayout = self.makeFormLayout(box)
        self.fill(box, formLayout, labels, widgets, 200, 70)
        parent.layout().addWidget(box)
        return box


    def fillInterestingIonsBox(self, parent):
        '''
        Constructs a QGroupBox and fills it with QCheckBoxes with fragment types. The analysis is based on the checked
        fragment types.
        '''
        box = QtWidgets.QGroupBox(parent)
        box.setGeometry(QtCore.QRect(5, 10, 320, 90))
        gridLayout = QtWidgets.QGridLayout(box)
        gridLayout.setContentsMargins(0,0,0,0)
        gridLayout.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)
        box.setTitle(self._translate(self.objectName(), "interesting ions"))
        box.setToolTip(self._translate(self.objectName(), "tick fragment types which should be more deeply analysed"))
        column = 0
        row = 0
        interestingIons = self._configHandler.get('interestingIons')
        known = ('a', 'b', 'c', 'd', 'w', 'x', 'y', 'z')
        new = [type for type in interestingIons if type not in known]
        for key in known:
            checkbox = QtWidgets.QCheckBox(box)
            '''if column < 4:
                checkbox.setGeometry(QtCore.QRect(10+int(column/2)*70, 30+(column%2)*30 , 50, 20))
            else:
                checkbox.setGeometry(QtCore.QRect(60+int(column/2)*70, 30+(column%2)*30 , 50, 20))'''
            if column==4:
                row=1
                column=0
            checkbox.setText(self._translate(self.objectName(), key))
            checkbox.setObjectName(key)
            if key in interestingIons:
                checkbox.setChecked(True)
            #checkbox.setMaximumWidth(15)
            self._interestingIons.append(checkbox)
            gridLayout.addWidget(checkbox,row,column)
            column +=1

        spacer = QtWidgets.QLabel(box)
        spacer.setMaximumHeight(10)
        gridLayout.addWidget(spacer,3,0)
        label = QtWidgets.QLabel(box)
        label.setMaximumHeight(25)
        label.setText(self._translate(self.objectName(), 'User defined ions:'))
        gridLayout.addWidget(label,4,0,1,-1)
        for i in range(4):
            lineEdit = QtWidgets.QLineEdit(box)
            lineEdit.setMaximumWidth(25)
            lineEdit.setToolTip(self._translate(self.objectName(), "Define you own type"))
            index = len(new)-i-1
            if index >= 0:
                lineEdit.setText(self._translate(self.objectName(), new[index]))
            self._addIons.append(lineEdit)
            gridLayout.addWidget(lineEdit,5,i)
        parent.layout().addWidget(box)
        return box


    def setupUi(self, configDialog):
        configDialog.move(200,100)
        self._spectrumTab = self.createTab("Spectrum")
        self._findingTab = self.createTab("Finding")
        self._modellingTab = self.createTab("Modelling")
        #self._threshold2Tab = self.createTab("thresholds 2")
        self._outputTab = self.createTab("Analysis/Output")
        self._mzBox = self.fillBox(self._spectrumTab, "m/z area containing peaks", ("min. m/z", "min. max. m/z", "tolerance", "window size"),
                        {"lowerBound": (QtWidgets.QSpinBox(),"lower m/z bound (just peaks with higher m/z are examined)"),
                         "minUpperBound":(QtWidgets.QSpinBox(), "minimal upper m/z bound"),
                         "upperBoundTolerance": (QtWidgets.QSpinBox(),
                                                "value is added to calculated upper m/z-bound for final value"),
                         "upperBoundWindowSize": (QtWidgets.QDoubleSpinBox(),
                                                   "window size for noise calculation to find upper m/z bound")})
        self._calibrationBox = self.fillBox(self._spectrumTab, "Autocalibration",
                            ("uncal. error threshold", "max. std. dev.",'overwrite peak list'),
                            {"errorLimitCalib": (QtWidgets.QSpinBox(), "max. ppm error in uncalbratied spectrum"),
                             "maxStd": (QtWidgets.QDoubleSpinBox(), "max. allowed standard deviation of the ion errors "
                                                                    "for the calibration"),
                             "overwrite": (QtWidgets.QCheckBox(), "the peak list will be overwritten if checked "
                                              '(otherwise the calibrated list will be written to a file with the old filename "+_cal")')})
        self._widgets['lowerBound'].setMaximum(9999)
        self._widgets['minUpperBound'].setMaximum(9999)
        self._widgets['upperBoundTolerance'].setMaximum(999)

        self._errorBox=self.fillBox(self._findingTab, "error threshold: threshold [ppm] = k/1000 * (m/z) +d",
                            ("charge tolerance", "error threshold k", "error threshold d", "tolerance for isotope peaks"),
                            {"zTolerance": (QtWidgets.QDoubleSpinBox(),"ions with charge states between the calculated "
                                                                       "charge +/- tolerance will be searched for"),
                             "k": (QtWidgets.QDoubleSpinBox(), "slope of ppm error threshold function"),
                             "d": (QtWidgets.QDoubleSpinBox(), "intercept of ppm error threshold function"),
                             "errorTolerance": (QtWidgets.QDoubleSpinBox(),"tolerance for isotope peak search in ppm")})
        self._widgets["d"].setMinimum(-9.99)
        #self._qualityBox = QtWidgets.QGroupBox(self._modellingTab)

        self._noiseBox = self.fillBox(self._findingTab, "noise calculation", ("window size", "noise threshold tolerance"),
                                      {"noiseWindowSize": (QtWidgets.QDoubleSpinBox(),"window size for noise calculation"),
                                       "thresholdFactor": (QtWidgets.QDoubleSpinBox(),
                                                           "set it lower to search for more isotope peaks")})
        self._isoPatternBox = self.fillBox(self._modellingTab, "isotope pattern calculation",
                                          ("min. proportion", "approximation"),
                                          {"maxIso": (QtWidgets.QDoubleSpinBox(),
                                                      "the calculation of the isotope peaks will be stopped when "
                                                      "their summed abundances are higher than the stated proportion"),
                                           "approxIso": (QtWidgets.QSpinBox(),"enter the number of the last isotope "
                                                                              "peak that should be exactly calculated")
                                           })
        self._widgets["maxIso"].setDecimals(3)
        self._widgets["maxIso"].setMaximum(0.999)
        self._modellingBox = self.fillBox(self._modellingTab, "modelling",
                            ("outlier peak threshold","max. nr. of overlapping ions","overlap threshold"),
                            {"outlierLimit": (QtWidgets.QDoubleSpinBox(),
                             "isotope peaks with higher values are not used for intensity modelling"),
                             "manualDeletion": (QtWidgets.QSpinBox(),"if more ions are overlapping in one pattern, the "
                                                                     "program will ask the user to manually delete ions"),
                             "overlapThreshold": (QtWidgets.QDoubleSpinBox(),
                                                  "ions which have a lower proportion in overlap pattern are deleted")})

        self._widgets["manualDeletion"].setMinimum(1)
        self._qualityBox = self.fillBox(self._outputTab, "Quality thresholds",
                                        ("quality (deletion)","quality (highlighting)","score (highlighting)", 'S/N (deletion)'),
                        {"shapeDel": (QtWidgets.QDoubleSpinBox(),"ions which have a higher value will be deleted"),
                         "shapeMarked": (QtWidgets.QDoubleSpinBox(), "ions which have a higher value will be highlighted"),
                         "scoreMarked": (QtWidgets.QDoubleSpinBox(),"ions which have a higher value will be highlighted"),
                         "SNR": (QtWidgets.QDoubleSpinBox(),"ions which have a lower signal-to-noise ratio will be deleted")})
        self._analysisBox = self.fillBox(self._outputTab, "Analysis", ("Use Abundances (int./z)",),
                                        {"useAb": (QtWidgets.QCheckBox(),
                                                   "Ticked if the abundaces (int./z) of the ions should be used for the "
                                                   "quantitative analysis. Otherwise, the intensities (int.) are used.")})
        self._interestingIonsBox = self.fillInterestingIonsBox(self._outputTab)
        self._verticalLayout.addWidget(self._buttonBox, 0, QtCore.Qt.AlignHCenter)
        self.backToLast()
        '''for fragItem in self._interestingIons:
            if fragItem.objectName() in (self._configHandler.get('interestingIons')):
                fragItem.setChecked(True)'''
        self._tabWidget.setCurrentIndex(3)


    def accept(self):
        newConfigurations = self.makeDictToWrite()
        interestingIons = list()
        for fragItem in self._interestingIons:
            if fragItem.isChecked():
                interestingIons.append(fragItem.objectName())
            for item in self._addIons:
                text = item.text()
                if (text != '') and (text not in interestingIons):
                    interestingIons.append(text)
        newConfigurations['interestingIons'] = interestingIons
        self._configHandler.write(newConfigurations)
        super(ConfigurationDialog, self).accept()


