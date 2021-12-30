
"""import os
import pathlib
import sys


if getattr(sys, 'frozen', False):
    path = os.path.dirname(sys.executable)
    pos = path.find('FAST MS')
    if pos != -1:
        path = path[:pos+len('FAST MS')] #+ '/'
    #print('yes', path)
else:
    #path = os.getcwd()
    #print("path:",path, os.path.dirname(__file__))
    path = pathlib.Path(__file__).resolve().parent.parent
    #path = os.path.dirname(__file__)
    pos = path.find('src')
    if pos != -1:
        path = path[:pos] #+ '/'
    elif 'tests' in path:
        path = path[:os.getcwd().find('tests')]
    else:
        path = os.path.join(path,'FAST MS')  #+ '/'
    #print('no', path)"""

'''path2 = os.path.dirname(sys.executable)
pos = path2.find('FAST MS')
path2 = os.path.dirname(sys.executable)
if pos != -1:
    path2 = path[:pos+len('FAST MS')]
print('hey',path2)'''
    #print("new path", path)"""
