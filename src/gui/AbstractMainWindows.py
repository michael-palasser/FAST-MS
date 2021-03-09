from PyQt5 import QtWidgets, QtCore


class AbstractMainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent, title):
        super(AbstractMainWindow, self).__init__(parent)
        self._translate = QtCore.QCoreApplication.translate
        self.mainWindow.setWindowTitle(self._translate(self.objectName(), title))
        self.centralwidget = QtWidgets.QWidget(self.mainWindow)
        self.mainWindow.setCentralWidget(self.centralwidget)

    def updateComboBox(self, comboBox, newOptions):
        toAdjust = comboBox.count() - len(newOptions)
        if toAdjust > 0:
            [comboBox.removeItem(i) for i in range(len(newOptions), len(newOptions) + toAdjust)]
        elif toAdjust < 0:
            [comboBox.addItem("") for i in range(-1 * toAdjust)]
        for i, option in enumerate(newOptions):
            comboBox.setItemText(i, self._translate(self.mainWindow.objectName(), option))

    def makePushBtn(self, parent, name, fun):
        button = QtWidgets.QPushButton(parent)
        sizePolicy = self.setNewSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHeightForWidth(self._defaultButton.sizePolicy().hasHeightForWidth())
        button.setSizePolicy(sizePolicy)
        #self._defaultButton.setMinimumSize(QtCore.QSize(113, 0))
        button.setText(self._translate(self.objectName(), name))
        button.clicked.connect(fun)
