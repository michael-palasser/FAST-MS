from PyQt5 import QtWidgets, QtCore
import numpy as np
import pandas as pd

from src.gui.GUI_functions import createComboBox, connectTable
from src.gui.widgets.IonTableWidgets import IonTableWidget, TickIonTableWidget
from src.gui.tableviews.ShowPeaksViews import SimplePeakView
from src.gui.widgets.SpectrumView import SpectrumView


class AbstractIonView(QtWidgets.QDialog):
    '''
    Dialog which shows overlapping ion patterns. Superclass of CheckMonoisotopicOverlapView and CheckOverlapsView
    '''
    def __init__(self,  patterns, title, message, widths, spectrum):
        super(AbstractIonView, self).__init__()
        self.setUpUi(title)
        self._patterns = []
        for pattern in patterns:
            self._patterns.append({self.hash(ion): ion for ion in pattern})
        self._widths = widths
        self._tables = []
        self._spectrum = spectrum
        label = QtWidgets.QLabel(self)
        label.setGeometry(QtCore.QRect(20, 20, 400, 16))
        label.setText(self._translate(self.objectName(), message))
        self._verticalLayout.addWidget(label)
        self._verticalLayout.addSpacing(12)
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
        else:
            finall_y = yPos
        self._dumpList = []

        self._scrollArea.setWidget(self._contents)
        self._scrollArea.resize(width + 90, finall_y - 10)
        self._verticalLayout.addWidget(self._scrollArea)
        finall_y = self.makeButtonBox(width, finall_y+90)
        self.resize(width + 130, finall_y + 20)
        self._canceled = False
        self.show()

    def canceled(self):
        return self._canceled

    def makeTables(self, yPos):
        return yPos

    def connectTable(self, table):
        connectTable(table, self.showOptions)

    @staticmethod
    def hash(ion):
        return ion.getHash()

    def setUpUi(self, title):
        self._verticalLayout = QtWidgets.QVBoxLayout(self)
        self._translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(self._translate(self.objectName(), title))
        self._scrollArea = QtWidgets.QScrollArea(self)
        self._contents = QtWidgets.QWidget()
        self._formlayout = QtWidgets.QFormLayout(self._contents)
        self._formlayout.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)
        #self._contents.setLayout(self._formlayout)
        self._scrollArea.setGeometry(QtCore.QRect(20, 60, 361, 161))
        #self._scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._scrollArea.setWidgetResizable(True)

    def makeButtonBox(self, width, yPos):
        self._buttonBox = QtWidgets.QDialogButtonBox(self)
        self._buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok)
        self._buttonBox.accepted.connect(self.accept)
        self._buttonBox.rejected.connect(self.reject)
        self._buttonBox.move(width - self._buttonBox.width() - 50, yPos)
        self._verticalLayout.addWidget(self._buttonBox)
        return yPos + 30

    def accept(self):
        super(AbstractIonView, self).accept()

    def reject(self):
        choice = QtWidgets.QMessageBox.question(self, 'Closing ',
            "Unsaved Results!\nDo you really want to cancel?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if choice == QtWidgets.QMessageBox.Yes:
            self._canceled = True
            super(AbstractIonView, self).reject()

    def getDumplist(self):
        return self._dumpList

    def showOptions(self, table, pos):
        global view
        it = table.itemAt(pos)
        if it is None:
            return
        selectedRow = it.row()
        columnCount = table.columnCount()
        item_range = QtWidgets.QTableWidgetSelectionRange(0, selectedRow, columnCount - 1, selectedRow)
        table.setRangeSelected(item_range, True)
        menu = QtWidgets.QMenu()
        showAction = menu.addAction("Show in Spectrum")
        peakAction = menu.addAction("Show Peaks")
        copyAllAction = menu.addAction("Copy Table")
        copyAction = menu.addAction("Copy Cell")
        action = menu.exec_(table.viewport().mapToGlobal(pos))
        if action == showAction:
            ions = self.getIons(table)
            minLimit, maxLimit, YLimit = self.getLimits(ions)
            peaks = self._spectrum[
                np.where((self._spectrum[:, 0] > (minLimit - 5)) & (self._spectrum[:, 0] < (maxLimit + 5)))]

            view = SpectrumView(None, peaks, ions, minLimit, maxLimit, YLimit)
        elif action == peakAction:
            global peakview
            peakview = SimplePeakView(None, table.getIon(selectedRow))
        elif action == copyAction:
            it = table.indexAt(pos)
            if it is None:
                return
            selectedCol = it.column()
            df = pd.DataFrame([table.getIonValues()[selectedRow][selectedCol]])
            df.to_clipboard(index=False, header=False)
        elif action == copyAllAction:
            df = pd.DataFrame(data=table.getIonValues(), columns=table.getHeaders())
            df.to_clipboard(index=False, header=True)

    def getIons(self, *args):
        index = None
        for i, t in enumerate(self._tables):
            if t == args[0]:
                index = i
        return self._patterns[index].values()

    @staticmethod
    def getLimits(ions):
        '''
        Returns the min and max m/z value and the max relAb of the ions in a table
        :param (list[FragmentIon]) ions:
        :return:
        '''
        minLimit = 4000
        maxLimit = 0
        YLimit = 0
        for ion in ions:
            isoPattern = ion.getIsotopePattern()
            minMz = np.min(isoPattern['m/z'])
            maxMz = np.max(isoPattern['m/z'])
            maxY = np.max(isoPattern['relAb'])
            if minLimit > minMz:
                minLimit = minMz
            if maxLimit < maxMz:
                maxLimit = maxMz
            if YLimit < maxY:
                YLimit = maxY
        return minLimit, maxLimit, YLimit



class CheckOverlapsView(AbstractIonView):
    '''
    Dialog which shows overlapping ion patterns in multiple TickIonTableWidgets. Ticked ions are deleted after closing
    the dialog.
    '''
    def __init__(self, patterns, spectrum):
        super(CheckOverlapsView, self).__init__(patterns, "Check Overlapping Ions",
           "Complex overlapping patterns - Select ions for deletion:", [100, 30, 120, 140, 70, 60, 60,40], spectrum)

    def makeTables(self, yPos):
        for i, pattern in enumerate(self._patterns):
            table = TickIonTableWidget(self._contents, pattern.values(), yPos) #self.createTableWidget(self, pattern, yPos)
            for i,width in enumerate(self._widths):
                table.setColumnWidth(i,width)
            #self.formLayout.setWidget(i+1, QtWidgets.QFormLayout.SpanningRole, table)  # ToDo
            self.connectTable(table)
            self._tables.append(table)
            yPos += len(pattern.values())*20+50
            self._formlayout.addWidget(table)
            spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
            self._formlayout.addItem(spacerItem)
        return yPos

    def accept(self):
        for table in self._tables:
            self._dumpList += table.getDumpList()
        super(CheckOverlapsView, self).accept()


class CheckMonoisotopicOverlapView(AbstractIonView):
    '''
    Dialog which shows overlapping ion patterns (same molecular mass and charge) in multiple IonTableWidgets.
    Correct ions are selected by the user using a QComboBox.
    '''
    def __init__(self, patterns, spectrum):
        self._comboBoxes = []
        self._optionDict = dict()
        super(CheckMonoisotopicOverlapView, self).__init__(patterns, "Check Heavily Overlapping Ions",
           "These ions have the same mass - select the ion you want to keep", [100, 30, 120, 140, 70, 60, 60], spectrum)

    def makeTables(self, yPos):
        for i, pattern in enumerate(self._patterns):
            self.makeComboBox(pattern.values(),yPos)
            table = IonTableWidget(self._contents, pattern.values(), yPos + 40)
            for i,width in enumerate(self._widths):
                table.setColumnWidth(i,width)
            self.connectTable(table)
            self._tables.append(table)
            yPos += len(pattern.values())*20+50+50
            self._formlayout.addWidget(table)
            spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
            self._formlayout.addItem(spacerItem)

        return yPos

    def makeComboBox(self, pattern, yPos):
        options = []
        for ion in pattern:
            key = ion.getName()+",    " + str(ion.getCharge())
            options.append(key)
            self._optionDict[key] = ion
        comboBox = createComboBox(self._contents, options)
        #comboBox.setGeometry(QtCore.QRect(30, yPos, 180, 26))
        comboBox.setToolTip("Select the ion which you want to keep, the others will be deleted")
        self._comboBoxes.append(comboBox)
        self._formlayout.addWidget(comboBox)

    """def hashRow(self, row):
        return (row[3],row[1])"""

    def accept(self):
        ionsToKeep = []
        for box in self._comboBoxes:
            ionsToKeep.append(self._optionDict[box.currentText()])
        for pattern in self._patterns:
            for ion in pattern.values():
                if ion not in ionsToKeep:
                    self._dumpList.append(ion)
        super(CheckMonoisotopicOverlapView, self).accept()


