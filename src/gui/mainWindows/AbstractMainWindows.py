import os
from PyQt5 import QtWidgets, QtCore

from src.gui.GUI_functions import translate, setIcon
from src.resources import autoStart, path


class SimpleMainWindow(QtWidgets.QMainWindow):
    '''
    Used by TD_searchController, EditorControllers; parent class of StartWindow, IsotopePatternView
    '''
    def __init__(self, parent, title, centralWidget = None):
        super(SimpleMainWindow, self).__init__(parent)
        self._translate = translate
        self.setWindowTitle(self._translate(self.objectName(), title))
        if centralWidget is None:
            self._centralwidget = QtWidgets.QWidget(self)
        else:
            self._centralwidget = centralWidget(self)
        self.setCentralWidget(self._centralwidget)
        setIcon(self)
        #self.setWindowIcon(QIcon(os.path.join(path, 'icon.ico')))

    def updateComboBox(self, comboBox, newOptions,empty=False):
        """optionLength = len(newOptions)
        toAdjust = comboBox.count() - optionLength
        if toAdjust > 0:
            [comboBox.removeItem(optionLength) for i in range(optionLength, optionLength + toAdjust)]
        elif toAdjust < 0:
            [comboBox.addItem("") for i in range(-1 * toAdjust)]
        print(comboBox.count())
        for i, option in enumerate(newOptions):
            comboBox.setItemText(i, self._translate(self.objectName(), option))"""
        comboBox.clear()
        if empty:
            newOptions=[""] + newOptions
        comboBox.addItems(newOptions)

    def createMenuBar(self):
        self._menubar = QtWidgets.QMenuBar(self)
        self.setMenuBar(self._menubar)
        self._menubar.setGeometry(QtCore.QRect(0, 0, 340, 22))

    def createMenu(self, name, options, separatorPosition, icon=None):
        '''
        Makes a QMenu
        :param name: name of the menu
        :param dict[str,tuple[Callable,str,str]] options: options of the menu (dict of name : (function, tooltip, shortcut))
        :param (int | None) separatorPosition: position of a separator
        '''
        menu = QtWidgets.QMenu(self._menubar)
        menu.setTitle(self._translate(self.objectName(), name))
        menu.setToolTipsVisible(True)
        menuActions = dict()
        pos = len(options)
        if icon is not None:
            menu.setIcon(icon)
        for option, vals in options.items():
            function, tooltip, shortcut = vals
            if separatorPosition != None and pos == separatorPosition:
                menu.addSeparator()
            action = QtWidgets.QAction(self)
            action.setText(self._translate(self.objectName(),option))
            if tooltip is not None:
                action.setToolTip(tooltip)
            if shortcut != None:
                action.setShortcut(shortcut)
            action.triggered.connect(function)
            menuActions[option] = action
            menu.addAction(action)
            pos -= 1
        self._menubar.addAction(menu.menuAction())
        return menu, menuActions

    def makeHelpMenu(self):
        manual = os.path.join(path, 'FAST MS Manual.pdf')
        paper = os.path.join(path, 'palasser-breuker-2024-fast-ms-software-for-the-automated-analysis-of-top-down-mass-spectra-of-polymeric-molecules.pdf')
        self.createMenu('Help',{'Manual':(lambda: autoStart(manual),'Open the Manual',None),
                                'Publication':(lambda: autoStart(paper),'Open the FAST MS publication',None),
                                'Citing FAST MS': (self.openRefWidget, "How to cite the programme", None)},None)

    def openRefWidget(self):
        global refWidget
        refWidget = QtWidgets.QWidget(None)
        layout = QtWidgets.QVBoxLayout(refWidget)
        text = "FAST MS: Software for the Automated Analysis of Top-Down Mass Spectra of Polymeric Molecules Including RNA, DNA, and Proteins<br>" \
               "Michael Palasser and Kathrin Breuker<br>" \
               "Journal of the American Society for Mass Spectrometry Article ASAP<br>" \
               "DOI: 10.1021/jasms.4c00236"
        label = QtWidgets.QLabel(refWidget)
        label.setText(text)
        label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        layout.addWidget(label)
        refWidget.setWindowTitle("Citing FAST MS")
        refWidget.show()
        return refWidget

