# for i in range(0,10,1):
#     print(i)
# for i in range(0,10,2):
#     print(f"Even Number is {i}")

# # Table
# a = int(input("Enter the number :- "))
# for i in range(1,11,1):
#     print(f"{i} x {a} = {i*a}")
# print("Printing is Done!")

# Prime Number:
a = int(input("Enter a Number :- "))
for i in range(2,a//2):
    if(a%i==0):
        print(f"{a} is not a prime number!")
        break
    else:
        continue
print(f"{a} is a prime number!")