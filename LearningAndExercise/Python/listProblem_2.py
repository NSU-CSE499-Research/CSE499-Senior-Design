idex = 0
maxx =0
List = [1,2,3,7,8,4,3,9,2,4]
for i in range(len(List)):
    if(List[i]>maxx):
        maxx=List[i]
        idex = i

print(f"The max value is:-{maxx} and its index is:- {idex}")