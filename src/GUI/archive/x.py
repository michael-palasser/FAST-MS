from src.MolecularFormula import MolecularFormula
from multiprocessing import Pool
from time import time

formulas = []
for i in range(1,40):
    #formulas.append(MolecularFormula({'C':int(i*4.93),'H':int(7.76*i),'N':int(i*1.36),'O':int(i*1.48),'S':int(i*0.04)}))
    formulas.append(MolecularFormula({'C':int(i*10),'H':int(20*i),'N':int(i*5),'O':int(i*4),'P':int(i)}))
#Proteine ab 60

def calculate(formulaList):
    patterns = []
    for formula in formulaList:
        #print(formula.formulaDict['C'])
        patterns.append(formula.calculateIsotopePattern())

def calculate2(formula):
    return formula.calculateIsotopePattern()
def job(num):
    return num * 2
#start1 = time()
#data1 = calculate(formulas)
#time1 = time()-start1
if __name__ == '__main__':
    start1 = time()
    data1 = calculate(formulas)
    time1 = time()-start1
    print("normal:",time1)

    start2 = time()
    p = Pool()
    data2 = p.map(calculate2, formulas)
    p.close()
    time2 = time()-start2
    print("multi:", time2)
    start3 = time()
    data3 = calculate(formulas)
    time3 = time()-start3
    print("normal:", time3)