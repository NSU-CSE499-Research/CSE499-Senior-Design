a = int(input("Enter your age:- "))
try: 
    if a < 18 or a > 60:
        raise ValueError("Sorry age restricted")
    else:
        print("Welcome to the clud dude!")
        
except Exception as errr:
    print(f"Error how!{errr}")

print("Hum kisise nahi darte hamara club hamara mazi!")