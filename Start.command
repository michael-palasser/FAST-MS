#!/usr/bin/env python3
import os
import pip

def checkInstallation(package):
    try:
        __import__(package)
    except ImportError:
        pip.main(['install', package])

for package in ['numpy', 'scipy', 'matplotlib', 'pandas', 'PyQt5', 'pyqtgraph', 'xlsxwriter','logging','multiprocessing', 'numba', 'math',
                'sqlite3','tqdm']:
    checkInstallation(package)
print('hey',os.path.realpath(__file__))
try:
    os.system("python -m src.gui.StartWindow")
except ModuleNotFoundError:
    print('wat')
    #os.system("python -m "+os.path.realpath(__file__)+".src.gui.StartWindow")
    os.system("python -m Start.command")
