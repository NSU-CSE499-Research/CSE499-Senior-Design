a = (1,1,1,2,3,4,4,4,5,6,7)
print(a)
d =  {}
print(type(d))
for i in a:
    if i in d.keys():
        d[i]+=1
    else:
        d[i] = 1

print(d)