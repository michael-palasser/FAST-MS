from functools import partial

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QMovie
from PyQt5.QtWidgets import QLabel, QMainWindow
import numpy as np

from src.views.IonTableWidget import IonTableWidget, TickIonTableWidget, FinalIonTable
from src.views.SpectrumView import SpectrumView


class LoadingWidget(QtWidgets.QWidget):
    def __init__(self):
        super(LoadingWidget, self).__init__()
        self.loading_lbl = QLabel(self)
        loading_movie = QMovie("loading.gif")  # some gif in here
        self.loading_lbl.setMovie(loading_movie)
        loading_movie.start()

        self.setGeometry(50, 50, 100, 100)
        self.setMinimumSize(10, 10)
        self.show()



class AbstractIonView(QtWidgets.QDialog):
    def __init__(self,  patterns, title, message, widths, spectrum):
        #self._dialog = QtWidgets.QDialog(parrent)
        super(AbstractIonView, self).__init__()
        self.setUpUi(title)
        self._patterns = []
        for pattern in patterns:
            self._patterns.append({self.hash(ion): ion for ion in pattern})
        #self.headers = ('m/z', 'z', 'I', 'fragment', 'error /ppm', 'S/N', 'qual.', 'del.?')
        self._widths = widths
        self._tables = []
        self._spectrum = spectrum
        label = QtWidgets.QLabel(self)
        label.setGeometry(QtCore.QRect(20, 20, 400, 16))
        label.setText(self._translate(self.objectName(), message))

        """self.loading_lbl = QLabel(self)
        #self.loading_lbl.setStyleSheet('border: 1px solid red')  # just for illustration
        #self.loading_lbl.setAlignment(QtCore.Qt.AlignCenter)
        #self..addWidget(self.loading_lbl)
        loading_movie = QMovie("loading.gif")
        self.loading_lbl.setMovie(loading_movie)
        loading_movie.start()
        self.show()"""
        #widget = LoadingWidget()
        #widget.exec_()
        yPos = 60
        yPos = self.makeTables(yPos)
        width = sum(self._widths)
        if yPos > 800:
            finall_y = 800
            #scrollBar = QtWidgets.QScrollBar(self.scrollArea)
            #self.resize(width + 80, 900)
        else:
            finall_y = yPos
            #self.scrollArea.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
            #self.scrollArea.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self._dumpList = []

        self.scrollArea.setWidget(self.contents)
        self.scrollArea.resize(width+90, finall_y-10)
        finall_y = self.makeButtonBox(width, finall_y+90)
        self.resize(width + 130, finall_y + 20)
        self.canceled = False
        self.show()

    def makeTables(self, yPos):
        return yPos

    def connectTable(self, table):
        table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        table.customContextMenuRequested['QPoint'].connect(partial(self.showOptions, table))

    @staticmethod
    def hash(ion):
        return (ion.getName(),ion.charge)

    def setUpUi(self, title):
        self.setObjectName("dialog")
        self._translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(self._translate(self.objectName(), title))
        self.scrollArea = QtWidgets.QScrollArea(self)
        self.contents = QtWidgets.QWidget()
        self.formlayout = QtWidgets.QFormLayout()
        self.contents.setLayout(self.formlayout)
        self.scrollArea.setGeometry(QtCore.QRect(20, 60, 361, 161))
        #self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scrollArea.setWidgetResizable(True)

    def makeButtonBox(self, width, yPos):
        self.buttonBox = QtWidgets.QDialogButtonBox(self)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.buttonBox.move(width - self.buttonBox.width() - 50, yPos)
        return yPos + 30

    def accept(self):
        super(AbstractIonView, self).accept()

    def reject(self):
        choice = QtWidgets.QMessageBox.question(self, 'Closing ',
            "Unsaved Results!\nDo you really want to cancel?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if choice == QtWidgets.QMessageBox.Yes:
            self.canceled = True
            super(AbstractIonView, self).reject()

    def getDumplist(self):
        return self._dumpList

    def showOptions(self, table, pos):
        global view
        """it = table.itemAt(pos)
        if it is None:
            return
        selectedRowIndex = it.row()
        columnCount = table.columnCount()
        item_range = QtWidgets.QTableWidgetSelectionRange(0, selectedRowIndex, columnCount - 1, selectedRowIndex)
        table.setRangeSelected(item_range, True)"""
        menu = QtWidgets.QMenu()
        showAction = menu.addAction("Show in Spectrum")
        action = menu.exec_(table.viewport().mapToGlobal(pos))
        if action == showAction:
            """index = None
            for i, t in enumerate(self._tables):
                if t == table:
                    index = i
            minLimit = 4000
            maxLimit = 0
            for ion in self._patterns[index].values():
                minMz = np.min(ion.isotopePattern['m/z'])
                maxMz = np.max(ion.isotopePattern['m/z'])
                if minLimit > minMz:
                    minLimit = minMz
                if maxLimit < maxMz:
                    maxLimit = maxMz"""
            ions = self.getIons(table)
            minLimit, maxLimit, YLimit = self.getLimits(ions)
            peaks = self._spectrum[np.where((self._spectrum[:,0]>(minLimit-5)) & (self._spectrum[:,0]<(maxLimit+5)))]
            view = SpectrumView(peaks, ions, minLimit, maxLimit, YLimit)

    def getIons(self, *args):
        index = None
        for i, t in enumerate(self._tables):
            if t == args[0]:
                index = i
        return self._patterns[index].values()

    @staticmethod
    def getLimits(ions):
        minLimit = 4000
        maxLimit = 0
        YLimit = 0
        for ion in ions:
            minMz = np.min(ion.isotopePattern['m/z'])
            maxMz = np.max(ion.isotopePattern['m/z'])
            maxY = np.max(ion.isotopePattern['relAb'])
            if minLimit > minMz:
                minLimit = minMz
            if maxLimit < maxMz:
                maxLimit = maxMz
            if YLimit < maxY:
                YLimit = maxY
        return minLimit, maxLimit, YLimit



class CheckOverlapsView(AbstractIonView):
    def __init__(self, patterns, spectrum):
        super(CheckOverlapsView, self).__init__(patterns, "Check Overlapping Ions",
           "Complex overlapping patterns - Select ions for deletion:", [100, 30, 120, 140, 70, 60, 60,40], spectrum)

    def makeTables(self, yPos):
        for i, pattern in enumerate(self._patterns):
            table = TickIonTableWidget(self.contents, pattern.values(), yPos) #self.createTableWidget(self, pattern, yPos)
            for i,width in enumerate(self._widths):
                table.setColumnWidth(i,width)
            #self.formLayout.setWidget(i+1, QtWidgets.QFormLayout.SpanningRole, table)  # ToDo
            self.connectTable(table)
            self._tables.append(table)
            yPos += len(pattern.values())*20+50
            self.formlayout.addWidget(table)
            spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
            self.formlayout.addItem(spacerItem)
        return yPos

    def accept(self):
        for table in self._tables:
            self._dumpList += table.getDumpList()
        print(self._dumpList)
        super(CheckOverlapsView, self).accept()


class CheckMonoisotopicOverlapView(AbstractIonView):
    def __init__(self, patterns, spectrum):
        self.comboBoxes = []
        self.optionDict = dict()
        super(CheckMonoisotopicOverlapView, self).__init__(patterns, "Check Heavily Overlapping Ions",
           "These ions have the same mass - select the ion you want to keep", [100, 30, 120, 140, 70, 60, 60], spectrum)

    def makeTables(self, yPos):
        for i, pattern in enumerate(self._patterns):
            self.makeComboBox(pattern.values(),yPos)
            table = IonTableWidget(self.contents, pattern.values(), yPos + 40)
            for i,width in enumerate(self._widths):
                table.setColumnWidth(i,width)
            self.connectTable(table)
            self._tables.append(table)
            yPos += len(pattern.values())*20+50+50
            self.formlayout.addWidget(table)
            spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
            self.formlayout.addItem(spacerItem)

        return yPos

    def makeComboBox(self, pattern, yPos):
        options = []
        for ion in pattern:
            key = ion.getName()+",    " + str(ion.charge)
            options.append(key)
            self.optionDict[key] = ion
        comboBox = QtWidgets.QComboBox(self.contents)
        for i, option in enumerate(options):
            comboBox.addItem("")
            comboBox.setItemText(i, self._translate(self.objectName(), option))
        comboBox.setGeometry(QtCore.QRect(30, yPos, 180, 26))
        comboBox.setToolTip("Select the ion which you want to keep, the others will be deleted")
        self.comboBoxes.append(comboBox)
        self.formlayout.addWidget(comboBox)

    """def hashRow(self, row):
        return (row[3],row[1])"""

    def accept(self):
        ionsToKeep = []
        for box in self.comboBoxes:
            ionsToKeep.append(self.optionDict[box.currentText()])
        for pattern in self._patterns:
            for ion in pattern.values():
                if ion not in ionsToKeep:
                    self._dumpList.append(ion)
        print(self._dumpList)
        super(CheckMonoisotopicOverlapView, self).accept()



class FinalIonView(AbstractIonView):
    def __init__(self, ions, spectrum):
        """lbl = QLabel()
        movie = QMovie("loading.gif")
        lbl.setMovie(movie)
        lbl.show()
        movie.start()"""
        super(FinalIonView, self).__init__((ions,), "Results", "Observed Ions:",
                                                               [100, 30, 120, 140, 70, 60, 60, 160, 40], spectrum)
        #movie.stop()

    def makeTables(self, yPos):
        self._ions = self._patterns[0]
        self.__table = FinalIonTable(self.contents, self._ions.values(), yPos)  # self.createTableWidget(self, pattern, yPos)
        for i, width in enumerate(self._widths):
            self.__table.setColumnWidth(i, width)
        # self.formLayout.setWidget(i+1, QtWidgets.QFormLayout.SpanningRole, table)  # ToDo
        self.connectTable(self.__table)
        yPos += len(self._ions.values()) * 20 + 50
        self.formlayout.addWidget(self.__table)
        return yPos


    def showOptions(self, table, pos):
        global view
        menu = QtWidgets.QMenu()
        showAction = menu.addAction("Show in Spectrum")
        action = menu.exec_(table.viewport().mapToGlobal(pos))

        it = table.itemAt(pos)
        if it is None:
            return
        selectedRowIndex = it.row()
        columnCount = table.columnCount()
        item_range = QtWidgets.QTableWidgetSelectionRange(0, selectedRowIndex, columnCount - 1, selectedRowIndex)
        table.setRangeSelected(item_range, True)
        selectedHash = (table.item(selectedRowIndex, 3).text(), int(table.item(selectedRowIndex, 1).text()))
        print(selectedHash)
        if action == showAction:
            ions = self.getIons(self._ions[selectedHash])
            print(ions)
            minLimit, maxLimit, maxY = self.getLimits(ions)
            peaks = self._spectrum[np.where((self._spectrum[:,0]>(minLimit-5)) & (self._spectrum[:,0]<(maxLimit+5)))]
            view = SpectrumView(peaks, ions, np.min(self._ions[selectedHash].isotopePattern['m/z']),
                                np.max(self._ions[selectedHash].isotopePattern['m/z']),
                                np.max(self._ions[selectedHash].isotopePattern['relAb']))


    def getIons(self, ion):
        monoisotopicDict = {ion.isotopePattern['m/z'][0]:key for key,ion in self._ions.items()}
        monoisotopics = np.array(sorted(list(monoisotopicDict.keys())))
        distance = 50
        median = ion.isotopePattern['m/z'][0]

        while True:
            monoisotopics = monoisotopics[np.where(abs(monoisotopics-median)<distance )]
            if len(monoisotopics)< 20:
                print(median,[monoisotopicDict[mono] for mono in monoisotopics])
                return [self._ions[monoisotopicDict[mono]] for mono in monoisotopics]
            elif len(monoisotopics)<30:
                distance /=1.5
            else:
                distance /=2
        #for hash, ion in self._patterns[0].items():

    def accept(self):
        self._dumpList += self.__table.getDumpList()
        print(self._dumpList)
        super(FinalIonView, self).accept()





