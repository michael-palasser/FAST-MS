l = []
ls = []
lsf = []
for i in range(20):
    nr = 4*i/3*(-1)**i
    l.append(round(nr,2))
    ls.append(str(round(nr,2)))
    lsf.append('{:6.2f}'.format(round(nr,2)))

print(sorted(l))
print(sorted(ls))
print(sorted(lsf))