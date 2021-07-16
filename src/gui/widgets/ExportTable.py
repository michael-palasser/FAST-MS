from PyQt5 import QtWidgets, QtCore


class ExportTable(QtWidgets.QTableWidget):
    '''
    QTableWidget which shows all ion values. To be exported a value have to be checked. The order of the row reflects
    the order of the columns in the exported document.
    '''
    def __init__(self, parent, options, stored):
        super(ExportTable, self).__init__(parent)
        self._headers = ('Value', 'Include')
        self._options = options#('m/z', 'z','intensity', 'fragment', 'error /ppm', 'S/N', 'quality', 'formula', 'score',
        #                 'comment', 'molecular mass', 'average mass', 'noise')
        self.setColumnCount(len(self._headers))
        self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.setRowCount(len(self._options))
        self.fill(stored)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self.setDragDropOverwriteMode(False)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        #self.setSelectionBehavior(QtGui.QAbstractItemView.SingleSelection)
        self.setHorizontalHeaderLabels(self._headers)
        self.setSortingEnabled(True)
        self.show()


    def fill(self, stored):
        '''
        Fills the table with the peak data
        '''
        #print(self.getValue(ion))
        for row, option in enumerate(self._options):
            items = [QtWidgets.QTableWidgetItem(option), QtWidgets.QTableWidgetItem()]
            if option in stored:
                items[1].setCheckState(QtCore.Qt.Checked)
            else:
                items[1].setCheckState(QtCore.Qt.Unchecked)
            for i in range(2):
                items[i].setTextAlignment(QtCore.Qt.AlignCenter)
                self.setItem(row, i, items[i])
        self.resizeRowsToContents()
        #self.resizeColumnsToContents()


    def dropEvent(self, event):
        '''
        Overwrites method of superclass. Ensures correct dragging of rows (without deleting other rows).
        '''
        if event.source() == self:
            rows = set([mi.row() for mi in self.selectedIndexes()])
            targetRow = self.indexAt(event.pos()).row()
            rows.discard(targetRow)
            rows = sorted(rows)
            if not rows:
                return
            if targetRow == -1:
                targetRow = self.rowCount()
            for _ in range(len(rows)):
                self.insertRow(targetRow)
            rowMapping = dict()  # Src row to target row.
            for idx, row in enumerate(rows):
                if row < targetRow:
                    rowMapping[row] = targetRow + idx
                else:
                    rowMapping[row + len(rows)] = targetRow + idx
            colCount = self.columnCount()
            for srcRow, tgtRow in sorted(rowMapping.items()):
                for col in range(0, colCount):
                    self.setItem(tgtRow, col, self.takeItem(srcRow, col))
            for row in reversed(sorted(rowMapping.keys())):
                self.removeRow(row)
            event.accept()
            self.resizeRowsToContents()
            return

    def readTable(self):
        options = []
        for row in range(self.rowCount()):
            if int(self.item(row, 1).checkState()/2)==1:
                options.append(self.item(row, 0).text())
        return options