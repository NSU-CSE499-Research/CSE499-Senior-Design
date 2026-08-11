# print(dir(list))
# help(list)

List = ["a",1,2,3,"b","c",'d','e',4.5,5.6,6.7,'end']
print(List)

# Append
List.append("Not End")
print(List)

# Insert
List.insert(0,"Start List")
print(List)

# remove(Value),pop(idx),index(idx),count(value),sort(),reverse(),copy(),clear
List.remove("end")
print(List)
List.pop(3)
print(List)
print(f"The value od d occerence is: {List.count('d')}")
List.reverse()
print(List)
List.clear()
print(List)