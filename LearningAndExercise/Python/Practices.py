# code for fibonacci series
def Fibonacci(num):
    f0 = 0
    f1 = 1 
    f2 = 1
    if num == 0:
        return 0
    elif num == 1 or num == 2:
        return 1
    else:
        f = 2
        f2 = 2
        for i in range(3,num,1):
            f = f1+f2
            f1 = f2
            f2 = f
        return f
def FibonacciSum(num):
    sum = 0
    for i in range(0,num+1,1):
        print(Fibonacci(i))
        sum += Fibonacci(i)
    return sum

a = int(input("Enter a Number :- "))
print(f"The {a}th Fibonacci Number is :- {Fibonacci(a)}") 
print(f"Sum of the fibonacci series is:- {FibonacciSum(a)}")