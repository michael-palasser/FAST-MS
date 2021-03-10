import subprocess

import numpy as np
import os

from src import path

def processVal(text):
    val = float(text)
    if val<0:
        val = 0
    return val


#subprocess.call(['open', path, 'amino.csv'])
#input('Press Enter')
file = os.path.join(path, 'amino.csv')
d = dict()
#data = np.loadtxt(file, delimiter=',', skiprows=1, usecols=[1, 2])
with open(file, 'r') as f:
    for i,line in enumerate(f):
        if i == 0:
            continue
        row = line.rstrip().split(',')
        print(row)
        if row[1] != '':
            val = processVal(row[1])
            if row[0] not in d.keys():
                d[row[0]] = [val]
            else:
                d[row[0]].append(val)
        if row[2] != '':
            val = processVal(row[2])
            if row[3] not in d.keys():
                d[row[3]] = [val]
            else:
                d[row[3]].append(val)

for key,vals in d.items():
    av = np.average(np.array([float(val) for val in vals if float(val) >= 0]))
    print(key, '\t', av)

