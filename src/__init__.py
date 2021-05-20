import os

path = os.getcwd()
#print("path:",path)
pos = os.getcwd().find('src')
if pos != -1:
    path = path[:pos] #+ '/'
elif 'tests' in path:
    path = path[:os.getcwd().find('tests')]
else:
    path = path #+ '/'
#print("new path", path)
