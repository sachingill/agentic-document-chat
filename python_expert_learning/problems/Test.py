
numbers = [1,2,3,4,5]

numbers.append(6)

for num in numbers:
    print(num * 2)


name = "Sachin"
print(name[0])

full_name = f"{name} Gill"


for chae in full_name:
    print(name)


user = {
    "name": "Sachin",
    "age": 30,
    "is_admin": True
}


print(user["name"])

user["locaiton"] = "India"


for key, val in user.items():
    print(f"{key}: {val}")

for i in range(5):
    print(i)


for i, val in enumerate(numbers):
    print(f"{i}: {val}")

text = "Hello, World!"

count = {}

for char in text:
    if char in count:
        count[char] += 1
    else:
        count[char] = 1



nums = [3, 7, 2, 9, 5]
max_num = nums[0]

for n in nums:
    if n > max_num:
        max_num = n


nums = [1, 2, 3, 4]
reversed_list = []

for i in range(len(nums)-1, -1, -1):


text = "hello"
rev = ""

for char in text:
    rev = char + rev
print(rev)


s = "madam"
is_palindrome = True

for i in range(len(s)//2):
    if s[i] != s[len(s)-1-i]:
        is_palindrome = False
        break   


text = "engineering"
vowels = "aeiou"
count = 0


for char in text:
    if char in vowels:
        count += 1
print(count)


text = "banana"
freq = {}

for char in text:
    freq[char] = freq.get(char,0) + 1

print(freq)

text = "swiss"
freq = {}

for char in  text:
    