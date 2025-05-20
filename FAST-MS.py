import sys
from multiprocessing import freeze_support

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication
import numpy.core.multiarray #ModuleNotFoundError: No module named 'numpy.core.multiarray' otherwise

from src.gui.GUI_functions import setIcon
from src.resources import INTERN

if INTERN:
    from src.BACHEM_extension.gui.StartWindow_BACHEM import InternalWindow as Window
else:
    from src.gui.StartWindow import Window


def run():
    global gui
    app = QApplication(sys.argv)
    app.setStyle(QtWidgets.QStyleFactory.create("Fusion"))
    app.setApplicationName("FAST MS")
    setIcon(app)
    gui = Window()
    sys.exit(app.exec_())

if __name__ == '__main__':
    freeze_support()  #Required for frozen executable: https://github.com/pyinstaller/pyinstaller/wiki/Recipe-Multiprocessing
    run()