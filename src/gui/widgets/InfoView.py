from PyQt5 import QtWidgets

from src.gui.GUI_functions import setIcon, translate


class InfoView(QtWidgets.QWidget):
    '''
    QWidget which shows the protocol text of a top-down search
    '''
    def __init__(self, parent, info):
        super(InfoView, self).__init__(parent)
        self._info = info
        self._translate = translate
        self.setWindowTitle(self._translate(self.objectName(), 'Protocol'))
        verticalLayout1 = QtWidgets.QVBoxLayout(self)
        scrollArea = QtWidgets.QScrollArea(self)
        verticalLayout1.addWidget(scrollArea)
        verticalLayout2 = QtWidgets.QVBoxLayout(scrollArea)
        self._text = QtWidgets.QTextEdit(scrollArea)
        self._text.setReadOnly(True)
        self._text.setText(self._translate(self.objectName(), self._info.toString()))
        scrollArea.setWidgetResizable(True)
        scrollArea.setWidget(self._text)
        verticalLayout2.addWidget(self._text)
        setIcon(self)
        self.show()

    def update(self):
        self._text.setText(self._translate(self.objectName(), self._info.toString()))