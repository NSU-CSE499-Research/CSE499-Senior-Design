from pathlib import Path

# Reading All File in Same folder
def ReadingFilesInFolder():
    path = Path('')
    items = list(path.rglob('*'))
    for i, items in enumerate(items):
        print(f"{i+1} : {items}")

def CreateFile():
    ReadingFilesInFolder()
    s = input("Enter your file name:- ")
    p = Path(s)
    with open(p,'w') as fs:
        data = input("Write whatever you want:- ")
        fs.write(data)
    

# Main Method: 
print("Enter 1 for creating a file")
print("Enter 2 for  reaging a file")
print("Enter 3 for updating a file")
print("Enter 4 for deleting a file")

a = int(input("Enter your option:- "))

if a == 1:
    CreateFile()
