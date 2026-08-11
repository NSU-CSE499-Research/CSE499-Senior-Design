# class Student:
#     def __init__(self,Sid,Name,Credit,CGPA):
#        self.Sid = Sid
#        self.Name = Name
#        self.Credit = Credit
#        self.CGPA = CGPA
#     def Show(self):
#         print(f"Your Student Info is : {self.Name},{ self.Sid}, {self.Credit}, {self.CGPA}")

# Student1 =Student(23127037,"F arhan",1171,3.297)

# Student2 = Student(2312703,"Farhan",111,3.29)

# Student1.Show()
# Student2.Show()
# print(type(Student1.CGPA))

# #Inheritance :

class Human:
    print("I am your dade!")
    def __init__(self, name):
        self.name = name
    def Print(self):
        print(f"Your name is : {self.name}")

class Animal(Human):
    pass

obj1 = Animal("Farhan ")
obj1.Print()

Simple Inheritance
class Animal:
    def __init__(self, name):
        self.name = name
    def Show(self):
        print(f"Your name is : {self.name}")

class Human(Animal):
    def __init__(self, name, age):
        super().__init__(name)
        self.age = age
    def Show(self):
        print(f"Your name is : {self.name} and age is : {self.age}")


O1 = Human("Farhan", 20)
O1.Show()

# Multiple Inheritanc
class Animal:
    name1 = "Lion"
class Human:
    name2 = "Sikder"
class Robot(Animal, Human):
    name3 = "Zico"

obj1 = Robot
print(obj1.name1)