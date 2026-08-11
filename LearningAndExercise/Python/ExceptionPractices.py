a = int(input("Enter a Number: "))
try:
    print(10/a)
except Exception as errr:
    print(f"Sorry you can't divide by {errr}")
else:
    print("Everything is ok dude")
finally:
    print("Mera gunda rajj calaga")
print("All worke done!")
