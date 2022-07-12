from os import system

import pip


def checkInstallation(package):
    try:
        __import__(package)
    except ImportError:
        pip.main(['install', package])

if __name__ == '__main__':
    for package in ['numpy', 'scipy', 'matplotlib', 'pandas', 'PyQt5', 'pyqtgraph', 'xlsxwriter', 'numba', 'tqdm']:
        checkInstallation(package)
    try:
        system("pyinstaller FAST-MS.py --clear")
    except ModuleNotFoundError:
        checkInstallation('pyinstaller')
        system("pyinstaller FAST-MS.py --clear")
    system("python -m src.gui.StartWindow")