List = [1,2,3,9,-2,-3,-90,99,10,7,8,-11]

List1 = []
List2 = []
for i in range(len(List)):
    if(List[i]>=0):
        List1.append(List[i])
    else:
        List2.append(List[i])
print(f"Positive List:- {List1}")
print(f"Negative List:- {List2}")