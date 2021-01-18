from src.MolecularFormula import MolecularFormula
from multiprocessing import Pool
from time import time

formulas = []
modifications = 1
losses = 2
#losses = 1
ions = 4
for i in range(1,35):
    for j in range((modifications+1)*(losses+1)+ions):
        #formulas.append(MolecularFormula({'C':int(i*4.93),'H':int(7.76*i),'N':int(i*1.36),'O':int(i*1.48),'S':int(i*0.04)}))
        formulas.append(MolecularFormula({'C':int(i*10),'H':int(20*i),'N':int(i*5),'O':int(i*4),'P':int(i)}))
#Proteine ab 50 bei 16
#RNA ab >30 bei 24
#insgesamt wenn liste>800

def calculate(formulaList):
    patterns = []
    for formula in formulaList:
        #print(formula.toString())
        #print(formula.formulaDict['C'])
        patterns.append(formula.calculateIsotopePattern())
    return patterns

def calculate2(formula):
    #print(formula.toString())
    return formula.calculateIsotopePattern()
def job(num):
    return num * 2
#start1 = time()
#data1 = calculate(formulas)
#time1 = time()-start1
"""if __name__ == '__main__':
    start1 = time()
    data1 = calculate(formulas)
    print(data1[-1])
    time1 = time()-start1
    print("normal:",time1)

    start2 = time()
    p = Pool()
    data2 = p.map(calculate2, formulas)
    print(data2[-1])
    p.close()
    time2 = time()-start2
    print("multi:", time2)
    start3 = time()
    data3 = calculate(formulas)
    print(data3[-1])
    time3 = time()-start3
    print("normal:", time3)"""


def checkName(name):
    print(name, name[0])
    #"ABC".islower()
    if (name[0].islower() or (len(name) > 1 and any(x.isupper() for x in name[1:]))):
        print("yes1")
        print("yes2")

checkName("He")
checkName("HeH")
checkName("he")
checkName("H")
print([["start",""]]+5*[["",""]])