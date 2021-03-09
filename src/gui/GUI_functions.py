
from PyQt5 import QtWidgets, QtCore

translate = QtCore.QCoreApplication.translate

def makeLabelInputWidget(parent,labelName,widget):
    horizontalWidget = QtWidgets.QWidget(parent)
    horizLayout = QtWidgets.QHBoxLayout(horizontalWidget)
    label = QtWidgets.QLabel(horizontalWidget)
    label.setText(translate(parent.objectName(), labelName))
    horizLayout.addWidget(label)
    horizLayout.addWidget(widget)
    return horizLayout

def createComboBox(parent, options):
    comboBox = QtWidgets.QComboBox(parent)
    for i, option in enumerate(options):
        comboBox.addItem("")
        comboBox.setItemText(i, translate(parent.objectName(), option))
    return comboBox


class AbstractMainWindow(QtWidgets.QMainWindow):
    def __init__(self, title):
        super(AbstractMainWindow, self).__init__()
        self._translate = QtCore.QCoreApplication.translate
        self.mainWindow.setWindowTitle(self._translate(self.objectName(), title))
        self.centralwidget = QtWidgets.QWidget(self.mainWindow)

        self.mainWindow.setCentralWidget(self.centralwidget)

    def createMenuBar(self, options):
        self.menubar = QtWidgets.QMenuBar(self.mainWindow)
        self.mainWindow.setMenuBar(self.menubar)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 340, 22))
        self.fileMenu, self.fileMenuActions = self.createMenu("File", options, 3)
        #self.editMenu, self.editMenuActions = self.createMenu("Edit", {"Insert Row": self.insertRow}, 1)
        self.menubar.addAction(self.fileMenu.menuAction())
        #self.menubar.addAction(self.editMenu.menuAction())


    def createMenu(self, name, options, *args):
        menu = QtWidgets.QMenu(self.menubar)
        menu.setTitle(self._translate(self.objectName(), name))
        menuActions = dict()
        pos = len(options)
        for option, function in options.items():
            if args and pos == args[0]:
                menu.addSeparator()
            action = QtWidgets.QAction(self)
            action.setText(self._translate(self.objectName(),option))
            '''if 'Open' in option:
                action.setShortcut("Ctrl+O")
            elif option == 'Save':
                action.setShortcut("Ctrl+S")
            elif option == 'Close':
                action.setShortcut("Ctrl+Q")'''
            action.triggered.connect(function)
            menuActions[option] = action
            menu.addAction(action)
            pos -= 1
        return menu, menuActions

    def createWidgetsInFormLayout(self, labels, widgets, initYPos, widgetWith, initialValues):
        """

        :param labels: list of Strings
        :param widgets: dict of {name:widget}
        :return:
        """
        maxWidth = 0
        yPos = initYPos
        for i, labelName in enumerate(labels):
            label = QtWidgets.QLabel(self.centralwidget)
            width = len(labelName)*10
            label.setGeometry(QtCore.QRect(20, yPos, width, 16))
            label.setText(self._translate(self.mainWindow.objectName(), labelName))
            self.formLayout.setWidget(i, QtWidgets.QFormLayout.LabelRole, label)
            if width>maxWidth:
                maxWidth = width
            #yPos += 30
        #yPos = initYPos
        self.widgets = dict()
        counter = 0
        for widgetName, widget in widgets.items():
            #widget = QtWidgets.QLineEdit(self.centralwidget)
            widget.setGeometry(QtCore.QRect(maxWidth+20, yPos, widgetWith, 21))
            self.formLayout.setWidget(counter, QtWidgets.QFormLayout.FieldRole, widget)
            self.widgets[widgetName] = widget
            #yPos += 30
            counter+=1
        for widget, initVal in zip(self.widgets.values(),initialValues):
            widget.setText(initVal) #self.pattern.getName()
        return counter


class AbstractDialog(QtWidgets.QDialog):
    def __init__(self, dialogName, title, lineSpacing, parent):
        super().__init__(parent)
        self.setObjectName(dialogName)
        self.lineSpacing = lineSpacing
        self.widgets = dict()
        #self.sizePolicy = self.setNewSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self._translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(self._translate(dialogName, title))
        self.buttonBox = QtWidgets.QDialogButtonBox(self)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.newSettings = None
        self.move(300,100)
        self.canceled = False