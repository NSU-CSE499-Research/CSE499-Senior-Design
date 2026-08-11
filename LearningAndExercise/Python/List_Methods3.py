# Second Largest 
H = 0
SH = 0
List = [1,2,3,7,8,4,3,9,2,4]
for i in range(len(List)):
    if(List[i]>H):
        SH = H
        H = List[i]

print(f"Height Number is: {H} and Second Height Number is: {SH}")