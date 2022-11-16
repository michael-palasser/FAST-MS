from multiprocessing.spawn import freeze_support

from src.gui.StartWindow import run


if __name__ == '__main__':
    freeze_support()
    run()