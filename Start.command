#!/usr/bin/env python3

import os
import sys
import pip

def checkInstallation(package):
    try:
        __import__(package)
    except ImportError:
        pip.main(['install', package])

for package in ['numpy', 'scipy', 'matplotlib', 'pandas', 'PyQt5', 'pyqtgraph', 'xlsxwriter','logging','multiprocessing', 'numba', 'math',
                'sqlite3','tqdm']:
    checkInstallation(package)
print(sys.executable)

abspath = os.path.abspath(__file__)
directory = os.path.dirname(abspath)
os.chdir(directory)
os.system("python -m src.gui.StartWindow")


#!/Users/eva-maria/.conda/envs/SAUSAGE_beta1/bin/python
