import os
import pathlib
import sys


if getattr(sys, 'frozen', False):
    path = os.path.dirname(sys.executable)
    pos = path.find('FAST MS')
    if pos != -1:
        path = path[:pos+len('FAST MS')]
else:
    path = pathlib.Path(__file__).resolve().parent.parent

def getRelativePath(relativePath, data=True):
    parent = pathlib.Path(__file__).resolve().parent
    if data:
        relPath = pathlib.Path('data') / relativePath
    else:
        relPath = pathlib.Path(relativePath)
    basePath = getattr(sys, '_MEIPASS', parent)
    #print(basePath / relPath)
    return basePath / relPath

