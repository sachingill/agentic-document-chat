# Generators: How to Use Them

## 🎯 The Problem

When you call a generator function, it **returns a generator object** - it doesn't execute the code immediately!

---

## ❌ Common Mistake

```python
def load_file_generator(file_path):
    with open(file_path, 'r') as f:
        for line in f:
            yield line.strip()

# ❌ This doesn't work - just returns generator object
load_file_generator("file.txt")  # Returns: <generator object at 0x...>
```

**Nothing happens!** The generator function doesn't execute until you iterate over it.

---

## ✅ How to Use Generators

### Method 1: Use a For Loop (Most Common)

```python
def load_file_generator(file_path):
    with open(file_path, 'r') as f:
        for line in f:
            yield line.strip()

# ✅ Iterate over the generator
for line in load_file_generator("file.txt"):
    print(line)  # Now it works!
```

### Method 2: Convert to List (If You Need All Items)

```python
# ✅ Convert generator to list
lines = list(load_file_generator("file.txt"))
print(lines)  # All lines in a list
```

**Warning**: This defeats the memory benefit of generators!

### Method 3: Use `next()` (One Item at a Time)

```python
# ✅ Get one item at a time
gen = load_file_generator("file.txt")
first_line = next(gen)  # Gets first line
second_line = next(gen)  # Gets second line
```

### Method 4: Use in List Comprehension

```python
# ✅ Use in comprehension
processed = [line.upper() for line in load_file_generator("file.txt")]
```

---

## 🔍 What's Happening Behind the Scenes

### Generator Function Call

```python
gen = load_file_generator("file.txt")
print(gen)  # <generator object load_file_generator at 0x...>
```

**Nothing executed yet!** Just created the generator object.

### Iterating Over Generator

```python
for line in gen:  # ← This triggers execution
    print(line)   # Now the code inside runs
```

**Now it executes!** Each iteration calls `next()` on the generator.

---

## 📝 Fixed Code Example

### Your Current Code (Not Working)

```python
def load_file_generator(file_path):
    with open(file_path, 'r') as f:
        for line in f:
            print(line)
            yield line.strip()

if __name__ == "__main__":
    load_file_generator("01_memory_profile.py")  # ❌ Just returns generator object
```

### Fixed Code (Working)

```python
def load_file_generator(file_path):
    with open(file_path, 'r') as f:
        for line in f:
            yield line.strip()  # Removed print - cleaner

if __name__ == "__main__":
    # ✅ Option 1: Iterate with for loop
    for line in load_file_generator("01_memory_profile.py"):
        print(line)
    
    # ✅ Option 2: Process lines
    for line in load_file_generator("01_memory_profile.py"):
        processed = line.upper()
        print(processed)
    
    # ✅ Option 3: Count lines (memory efficient!)
    line_count = sum(1 for _ in load_file_generator("01_memory_profile.py"))
    print(f"Total lines: {line_count}")
```

---

## 🎯 Complete Working Example

```python
def load_file_generator(file_path):
    """Generator that yields one line at a time"""
    with open(file_path, 'r') as f:
        for line in f:
            yield line.strip()

if __name__ == "__main__":
    file_path = "01_memory_profile.py"
    
    print("Method 1: Print all lines")
    print("=" * 50)
    for line in load_file_generator(file_path):
        print(line)
    
    print("\nMethod 2: Process lines")
    print("=" * 50)
    for line in load_file_generator(file_path):
        if line.startswith("def"):
            print(f"Found function: {line}")
    
    print("\nMethod 3: Count lines")
    print("=" * 50)
    count = sum(1 for _ in load_file_generator(file_path))
    print(f"Total lines: {count}")
    
    print("\nMethod 4: Get first 5 lines")
    print("=" * 50)
    gen = load_file_generator(file_path)
    for i in range(5):
        try:
            line = next(gen)
            print(f"Line {i+1}: {line}")
        except StopIteration:
            print("End of file")
            break
```

---

## 💡 Key Points

1. **Generator function returns generator object** - doesn't execute immediately
2. **Must iterate** to execute (for loop, list(), next(), etc.)
3. **Memory efficient** - only one item in memory at a time
4. **Lazy evaluation** - code executes only when needed

---

## ✅ Quick Fix for Your Code

```python
def load_file_generator(file_path):
    with open(file_path, 'r') as f:
        for line in f:
            yield line.strip()

if __name__ == "__main__":
    # ✅ Add for loop to iterate
    for line in load_file_generator("01_memory_profile.py"):
        print(line)
```

**Now it will work!** 🎉

