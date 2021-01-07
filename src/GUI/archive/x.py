from PyQt5 import QtCore, QtGui, QtWidgets

class Widget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(Widget, self).__init__(parent)

        self.table_widget = QtWidgets.QTableWidget(20, 10)

        for i in range(self.table_widget.rowCount()):
            for j in range(self.table_widget.columnCount()):
                it = QtWidgets.QTableWidgetItem("{}-{}".format(i, j))
                self.table_widget.setItem(i, j, it)

        vlay = QtWidgets.QVBoxLayout(self)
        vlay.addWidget(self.table_widget)

        self.table_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.table_widget.customContextMenuRequested.connect(self.on_customContextMenuRequested)

    @QtCore.pyqtSlot(QtCore.QPoint)
    def on_customContextMenuRequested(self, pos):
        it = self.table_widget.itemAt(pos)
        if it is None: return
        c = it.column()
        item_range = QtWidgets.QTableWidgetSelectionRange(0, c, self.table_widget.rowCount()-1 , c)
        self.table_widget.setRangeSelected(item_range, True)

        menu = QtWidgets.QMenu()
        delete_column_action = menu.addAction("Delete column")
        action = menu.exec_(self.table_widget.viewport().mapToGlobal(pos))
        if action == delete_column_action:
            self.table_widget.removeColumn(c)

if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    w = Widget()
    w.resize(640, 480)
    w.show()
    sys.exit(app.exec_())