import os
import pathlib
import sys
from platform import system
from re import search as reSearch
from subprocess import call

DEVELOP = False
INTERN = False
COMPILATION = False

if getattr(sys, 'frozen', False):
    path = os.path.dirname(sys.executable)
    pos = path.find('FAST MS')
    if pos != -1:
        path = path[:pos+len('FAST MS')]
    #if DEVELOP:
    #print("1",path)
else:
    path = pathlib.Path(__file__).resolve().parent.parent
    #if DEVELOP:
    #print("2",path)
for directory in ("Saved Analyses",'Fragment_lists'):
    dirPath = os.path.join(path, directory)
    if not os.path.isdir(dirPath):
        os.mkdir(dirPath)


def getRelativePath(relativePath, data=True):
    parent = pathlib.Path(__file__).resolve().parent
    #print(parent, parent.parent)
    if not os.path.isdir(parent):
        parent = parent.parent
    if data:
        relPath = pathlib.Path('data') / relativePath
        #print("1a",relPath, pathlib.Path('data'), relativePath)
        if DEVELOP:
            relPath = pathlib.Path('data_meins') / relativePath
        elif INTERN:
            relPath = pathlib.Path('data_BACHEM') / relativePath
    else:
        relPath = pathlib.Path(relativePath)
        #print("2a",relPath, pathlib.Path('data'), relativePath)
    basePath = getattr(sys, '_MEIPASS', parent)
    #print(basePath, basePath / relPath)
    return basePath / relPath


def autoStart(file):
    os_system = system()
    if os_system == 'Darwin':
        call(['open', file])
    elif os_system == 'Windows':
        os.startfile(file)
    else:
        call(('xdg-open', file))


def processTemplateName(templName):
    '''
    Splits the name of a template into species and modification
    :param (str) templName:
    :return: (tuple[str,str]) species, modification
    '''
    search = reSearch(r"([+,-])", templName)
    if search == None:
        return templName, ""
    # print('hey',templName[0:search.start()], templName[search.start():])
    return templName[0:search.start()], templName[search.start():]