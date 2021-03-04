from PyQt5 import QtCore, QtWidgets
from os.path import join

from src import path
from src.gui.AbstractDialogs import DialogWithTabs
from src.repositories.ConfigurationHandler import ConfigurationHandlerFactory

dataPath = join(path, 'src', 'data')


class TD_configurationDialog(DialogWithTabs):
    def __init__(self, parent):
        super().__init__(parent, "Configurations")
        self.configHandler = ConfigurationHandlerFactory.getTD_ConfigHandler()
        self.interestingIons = list()
        self.tabs = dict()
        self._boxSizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.setupUi(self)
        self.verticalLayout.addWidget(self.buttonBox, 0, QtCore.Qt.AlignRight)

    def createTab(self,name):
        tab = super(TD_configurationDialog, self).createTab(name)
        verticalLayout = QtWidgets.QVBoxLayout(tab)
        tab.setLayout(verticalLayout)
        return tab

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


