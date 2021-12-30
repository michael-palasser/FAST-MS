from os import system
import pip

def checkInstallation(package):
    try:
        __import__(package)
    except (ImportError, ModuleNotFoundError):
        pip.main(['install', package])

if __name__ == '__main__':
    for package in ['numpy', 'scipy', 'matplotlib', 'pandas', 'PyQt5', 'pyqtgraph', 'xlsxwriter','logging','multiprocessing', 'numba', 'math',
                    'sqlite3','tqdm']:
        checkInstallation(package)
    system("python -m src.gui.StartWindow")

#!/usr/bin/env python3
#print(sys.executable)

'''abspath = os.path.abspath(__file__)
directory = os.path.dirname(abspath)
os.chdir(directory)'''
#print(os.path.dirname(sys.executable), os.getcwd(),path)