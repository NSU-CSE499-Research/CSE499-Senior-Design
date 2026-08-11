a = [1,2,3,4,10,"Hello",10.4,"Hello World"]
print(a)
print(type(a))
print(a[1:6:2])
print(a[-1::-2])

# 1st way of access by index:

for i in range(len(a)):
    print(f"Index: {i} and Value: {a[i]}")

# 2nd way of access by value:

for i in a:
    print(i)