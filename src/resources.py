import os
import getpass
import pathlib
import sys
from platform import system
from re import search as reSearch
from subprocess import call
from datetime import datetime
import logging

DEVELOP = False
INTERN = False
COMPILATION = False

forbiddenCharacters = ("\\", "/", ":", "*", "?", '"', "<", ">", "|")

base_path = pathlib.Path(__file__).resolve().parent.parent
user = getpass.getuser()
for c in forbiddenCharacters:
    if c in user:
        user = user.replace(c, "")
if getattr(sys, 'frozen', False):
    base_path = base_path.parent
for directory in ("Saved Analyses",'Fragment_lists'):
    dirPath = os.path.join(base_path, directory)
    if not os.path.isdir(dirPath):
        os.mkdir(dirPath)

def getRelativePath(relativePath, data=True):
    if data:
        relPath = pathlib.Path('data') / relativePath
        if DEVELOP:
            relPath = pathlib.Path('data_meins') / relativePath
        elif INTERN:
            #relPath = pathlib.Path('data_BACHEM') / relativePath
            return pathlib.Path('//bagfa001/groupdata$/QC/QC_Early_Phase/EP12_MS Service/Tools/FAST-MS data/') / relativePath
    else:
        relPath = pathlib.Path(relativePath)
    return base_path / relPath

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

def processLongPaths(rawPath):
    newPath = str(rawPath).replace("/", "\\")
    if INTERN and newPath.startswith("I:"):
        newPath = newPath.replace("I:", r"\\bagfa001\groupdata$")
    if newPath.startswith("\\") and not newPath.startswith("\\\\"):
        newPath = "\\" + newPath
    if newPath.startswith('\\\\'):
        return os.path.normpath('\\\\?\\UNC\\' + newPath[2:])
    else:
        return os.path.normpath(newPath)


logFileBase = 'app_'+user+"_"+str(datetime.today().year)+"_"
logFilePath = os.path.join(base_path, logFileBase + str(datetime.today().month) + '.log')
if os.path.isfile(os.path.join(base_path, logFileBase + str(datetime.today().month - 1) + '.log')):
    os.remove(os.path.join(base_path, logFileBase + str(datetime.today().month - 1) + '.log'))
logging.basicConfig(filename=logFilePath, format='%(asctime)s - %(message)s', level=logging.INFO)
logging.info("Starting")
trainingTxt = "training_"+user+".txt"
try:
    if not os.path.isfile(trainingTxt) and not INTERN:
        autoStart(os.path.join(base_path,"FAST MS 1.1.0.pdf"))
        with open(trainingTxt, "w") as f:
            pass
except:
    print("Training file could not be opened")
    logging.warning(user+": training file could not be opened ("+trainingTxt+")")