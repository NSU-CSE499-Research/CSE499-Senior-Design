def Greeting(name):
    print(f"Hello mr. {name}")
Greeting("Farhan")

def Sum(a,b):
    return a+b
print(Sum(1,2))

def Talk(name="Unknown",age="Error!"):
    return f"Your name is {name} and your age is {age}."
s = Talk(name ="Farhan", age = "10")
print(Talk())