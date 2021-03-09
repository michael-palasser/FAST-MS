from PyQt5 import QtWidgets, QtCore


class LogFileView(QtWidgets.QWidget):
    def __init__(self, parent, logFile):
        super(LogFileView, self).__init__(parent)
        self._logFile = logFile
        self._translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(self._translate(self.objectName(), 'Log File'))
        verticalLayout1 = QtWidgets.QVBoxLayout(self)
        scrollArea = QtWidgets.QScrollArea(self)
        verticalLayout1.addWidget(scrollArea)
        verticalLayout2 = QtWidgets.QVBoxLayout(scrollArea)
        self._text = QtWidgets.QTextEdit(scrollArea)
        self._text.setReadOnly(True)
        self._text.setText(self._translate(self.objectName(), self._logFile.toString()))
        scrollArea.setWidgetResizable(True)
        scrollArea.setWidget(self._text)
        verticalLayout2.addWidget(self._text)
        self.show()

    def update(self):
        self._text.setText(self._translate(self.objectName(), self._logFile.toString()))