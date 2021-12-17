import os
import sys

if getattr(sys, 'frozen', False):
    path = os.path.dirname(sys.executable)
    pos = path.find('FAST MS')
    path = os.path.dirname(sys.executable)
    if pos != -1:
        path = path[:pos+len('FAST MS')] #+ '/'
    print('yes', path)
    path=os.path.dirname(sys.executable)
    print('yes', path)
else:
    path = os.getcwd()
    #print("path:",path)
    pos = path.find('src')
    if pos != -1:
        path = path[:pos] #+ '/'
    elif 'tests' in path:
        path = path[:os.getcwd().find('tests')]
    else:
        path = path #+ '/'

'''path2 = os.path.dirname(sys.executable)
pos = path2.find('FAST MS')
path2 = os.path.dirname(sys.executable)
if pos != -1:
    path2 = path[:pos+len('FAST MS')]
print('hey',path2)'''
    #print("new path", path)
