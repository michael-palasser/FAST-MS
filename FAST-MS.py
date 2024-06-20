from multiprocessing import freeze_support

from src.gui.StartWindow import run

if __name__ == '__main__':
    freeze_support()  #Required for frozen executable: https://github.com/pyinstaller/pyinstaller/wiki/Recipe-Multiprocessing
    run()