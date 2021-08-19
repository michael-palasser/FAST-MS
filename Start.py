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
os.system("python -m src.gui.StartWindow")