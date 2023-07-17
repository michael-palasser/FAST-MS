import pathlib
from re import findall
import json
from os.path import isfile, join
import sys
import numpy as np

import numpy as np
from PyQt5.QtWidgets import QApplication
from matplotlib import pyplot as plt
from PyQt5 import QtGui
import pyqtgraph as pg


helmSense = "{[mR](G)[sP].[mR](G)P.[mR](U)P.[mR](G)P.[mR](C)P.[mR](U)P.[mR](A)P.[fR](C)P.[fR](U)P.[fR](C)P.[fR](U)P.[mR](G)P.[mR](G)P.[mR](U)P.[mR](A)P.[mR](U)P.[mR](U)P.[mR](U)P.[mR](C)P.[mR](A)P.[mR](G)P.[mR](C)P.[mR](A)P.[mR](G)P.[mR](C)P.[mR](C)P.[mR](G)P.[Adem-GalNAc](A)P.[Adem-GalNAc](A)P.[Adem-GalNAc](A)P.[mR](G)P.[mR](G)P.[mR](C)P.[mR](U)P.[mR](G)P.[mR](C)}"
helmAntisense = "{[MeMOP](U)[sP].[fR](G)[sP].[fR](A)[sP].[fR](A)P.[fR](A)P.[mR](U)P.[fR](A)P.[mR](C)P.[mR](C)P.[fR](A)P.[mR](G)P.[mR](A)P.[mR](G)P.[fR](U)P.[mR](A)P.[mR](G)P.[mR](C)P.[mR](A)P.[mR](C)P.[mR](C)[sP].[mR](G)[sP].[mR](G)}"

fastmsSense = 'GmsGmUmGmCmUmAmCfUfCfUfGmGmUmAmUmUmUmCmAmGmCmAmGmCmCmGmAgalnacAgalnacAgalnacGmGmCmUmGmCm'
fastmsAntisense = 'UmpsGfsAfsAfAfUmAfCmCmAfGmAmGmUfAmGmCmAmCmCmsGmsGm'

nx218S_red = "WSGWSSCSRSCG"
nx218S_redLIMS = "H-Trp-Ser-Gly-Trp-Ser-Ser-Cys-Ser-Arg-Ser-Cys-Gly-OH" 
amg133 = "HAibEGTFTSDYSSYLEEQAAKEFIAWLVKGGGGGGGSGGGGSGGGGSKbrac"
amg133LIMS = "H-His-Aib-Glu-Gly-Thr-Phe-Thr-Ser-Asp-Tyr-Ser-Ser-Tyr-Leu-Glu-Glu-Gln-Ala-Ala-Lys-Glu-Phe-Ile-Ala-Trp-Leu-Val-Lys-Gly-Gly-Gly-Gly-Gly-Gly-Gly-Ser-Gly-Gly-Gly-Gly-Ser-Gly-Gly-Gly-Gly-Ser-Lys(bromoacetyl)-NH2" 
allSingle = "A	R	N	D	C	Q	E	G	H	I	L	K	M	F	P	S	T	W	Y	V	O	U"
allThree = "Ala	Arg	Asn	Asp	Cys	Gln	Glu	Gly	His	Ile	Leu	Lys	Met	Phe	Pro	Ser	Thr	Trp	Tyr	Val	Pyl	Sec"

def splitString(sequenceString):
    return sequenceString[1:-1].split(".")

def splitPepString(sequenceString):
    return sequenceString.split("-")[1:-1]
#def splitProteinString(sequenceString):


def splitFASTMSString(sequenceString):
    return findall('[A-Z][^A-Z]*', sequenceString)


sense1 = splitString(helmSense)
sense2 = splitFASTMSString(fastmsSense)
antisense1 = splitString(helmAntisense)
antisense2 = splitFASTMSString(fastmsAntisense)


def makeDict(*args):
    d = {}
    for seq in args:
        seq1 = splitFASTMSString(seq[0])
        seq2 = splitPepString(seq[1])
        for i in range(len(seq1)):
            d[seq1[i]] = seq2[i]
    l = sorted(list(d.keys()))
    newD ={key:d[key] for key in l} 
    return newD

def makeDict2(*args):
    d = {}
    seq1 = allSingle.split()
    seq2 = allThree.split()
    for i in range(len(seq1)):
        d[seq1[i]] = seq2[i]
    l = sorted(list(d.keys()))
    newD ={key:d[key] for key in l} 
    return newD

"""for i in range(len(sense1)):
    d[sense2[i]] = sense1[i]
for i in range(len(antisense1)):
    d[antisense2[i]] = antisense1[i]"""

d= makeDict((nx218S_red,nx218S_redLIMS),  (amg133,amg133LIMS))
d.update(makeDict2())
print(d)

aaD = {'A': 'Ala', 'R': 'Arg', 'N': 'Asn', 'D': 'Asp', 'C': 'Cys', 'E': 'Glu', 'Q': 'Gln', 'G': 'Gly', 'H': 'His', 'O': 'Pyl', 'I': 'Ile', 'L': 'Leu', 'K': 'Lys', 'M': 'Met', 'F': 'Phe', 'P': 'Pro', 'U': 'Sec', 'S': 'Ser', 'T': 'Thr', 'W': 'Trp', 'Y': 'Tyr', 'V': 'Val', 'Aib': 'Aib', 'Kbrac': 'Lys(bromoacetyl)'}
newAAD = {}
for aa in aaD.keys():
    newAAD[aaD[aa]] = aa
s = "Lys-Cys-Asn-Thr-Ala-Thr-Cys-Ala-Thr-Gln-Arg-Leu-Ala-Glu-Phe-Leu-Arg-His-Ser-Ser-Asn-Asn-Phe-Gly-Pro-Ile-Leu-Pro-Pro-Thr-Asn-Val-Gly-Ser-Asn-Thr-Pro"


newS = ""
for i in s.split("-"):
    newS += newAAD[i]
print(newS)

#path = pathlib.Path(__file__).resolve().parent.parent.parent
"""def write(parameters):
        '''
        Updates the configuration file
        :param (dict[str,Any]) parameters: new configurations
        '''
        with open(join(path, "data","RNA_dict"), "w") as f:
            json.dump(json.dumps(parameters, indent=3), f)"""

#write(newD)

"""colours = ['b','r','g']# ,'c', 'm', 'y']
markers = ['o','t', 's','p']# ,'h', 'star', '+', 'd', 'x', 't1','t2', 't3']


maxIndizes = (len(colours), len(markers))
coulour_index=0
marker_index=0
maxRow =0
for ion in range(10):
    print(colours, marker_index)
    marker_index+=1
    colours+=1
    if marker_index==maxIndizes[1]:
        marker_index=0
    if coulour_index==maxIndizes[0]:
        coulour_index=0
    coulour_index-=1
    if coulour_index< 0:
        marker_index=0
        maxRow +=1
        coulour_index=maxRow"""


def openXYFile(path, max_mz):
    rawData = []
    with open(path) as f:
        for line in f:
            rawData.append(tuple(line.rstrip().split()))
    rawData = np.array(rawData, dtype=[('m/z', float), ('I', float)])
    data = rawData[rawData['m/z']<max_mz]
    return data

path =pathlib.Path(__file__).resolve().parent.parent.parent.parent


def plot(vals):
    plot1 = pg.plot()
    plot1.setBackground('w')
    styles = {"black": "#f00", "font-size": "12pt"}
    plot1.setLabel('bottom', 'm/z', **styles)
    plot1.setLabel('left', 'Int.', **styles)
    for axis in ("left", "bottom"):
        font=QtGui.QFont()
        font.setPointSize(10)
        plot1.getAxis(axis).setStyle(tickFont=font)
        plot1.getAxis(axis).setTextPen("k")
    maxInt = np.max(vals["I"])
    yRange = (-0.005*maxInt, maxInt*1.05)
    curve = pg.PlotCurveItem(x=vals["m/z"],y=vals["I"],pen=pg.mkPen(color="k", width=0.5))
    plot1.plotItem.vb.setLimits(xMin=np.min(vals["m/z"]), xMax=np.max(vals["m/z"]), yMin=yRange[0], yMax=yRange[1])
    #newXVals, newVals = self.removeNANVals(xVals,vals)
    plot1.addItem(curve)

app = QApplication(sys.argv)

spectrum = openXYFile(join(path, "Spectral_data", "top-down","BI 3034701","MS009_23_0069 4+ 1725 opt","MS009_23_0069 83V_full.xy"),2500)
plot(spectrum)
sys.exit(app.exec_())