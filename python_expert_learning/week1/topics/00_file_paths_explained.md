# File Paths in Python - Explained

## 🎯 The Problem

You got this error:
```
FileNotFoundError: [Errno 2] No such file or directory: '01_memory_profile.py'
```

**Why?** The file `'01_memory_profile.py'` doesn't exist!

---

## 📁 Understanding File Paths

### Relative Paths

When you use a filename like `"memory_profile.py"`, Python looks for it **relative to where you run the script**.

```python
# This looks for file in current directory
with open("file.txt", 'r') as f:
    pass
```

**Current directory** = Where you run `python script.py` from

### Example

```bash
# If you run from /Users/sachin/nltk_data/api/
cd /Users/sachin/nltk_data/api/
python python_expert_learning/week1/exercises/memory_profile.py

# Python looks for "memory_profile.py" in:
# /Users/sachin/nltk_data/api/memory_profile.py  ❌ Wrong!
```

**But the file is actually at:**
```
/Users/sachin/nltk_data/api/python_expert_learning/week1/exercises/memory_profile.py
```

---

## ✅ Solutions

### Solution 1: Use Correct Filename

The file is called `"memory_profile.py"`, not `"01_memory_profile.py"`:

```python
# ✅ Correct
for line in load_file_generator("memory_profile.py"):
    print(line)
```

### Solution 2: Use Relative Path from Script Location

```python
import os

# Get directory where script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, "memory_profile.py")

for line in load_file_generator(file_path):
    print(line)
```

### Solution 3: Use Absolute Path

```python
# ✅ Full path
file_path = "/Users/sachin/nltk_data/api/python_expert_learning/week1/exercises/memory_profile.py"

for line in load_file_generator(file_path):
    print(line)
```

### Solution 4: Run from Correct Directory

```bash
# Change to the exercises directory first
cd /Users/sachin/nltk_data/api/python_expert_learning/week1/exercises/
python memory_profile.py
```

Now `"memory_profile.py"` will be found!

---

## 🔍 How to Check What Files Exist

### In Python:

```python
import os

# List files in current directory
files = os.listdir('.')
print("Files in current directory:")
for f in files:
    print(f"  - {f}")

# Check if file exists
if os.path.exists("memory_profile.py"):
    print("File exists!")
else:
    print("File not found!")
```

### In Terminal:

```bash
# List files
ls -la

# Check if file exists
ls memory_profile.py
```

---

## 💡 Best Practice: Use `__file__`

```python
import os

def load_file_generator(file_path):
    # If relative path, make it relative to script location
    if not os.path.isabs(file_path):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, file_path)
    
    with open(file_path, 'r') as f:
        for line in f:
            yield line.strip()
```

**This way**, the file path is always relative to where the script is, not where you run it from!

---

## 🎯 Quick Fix for Your Code

**The issue**: You're trying to open `"01_memory_profile.py"` which doesn't exist.

**The fix**: Use `"memory_profile.py"` (the actual filename):

```python
if __name__ == "__main__":
    # ✅ Use correct filename
    for line in load_file_generator("memory_profile.py"):
        print(line)
```

**Or** create a test file:

```python
if __name__ == "__main__":
    # Create test file
    with open("test.txt", 'w') as f:
        f.write("Line 1\nLine 2\nLine 3\n")
    
    # Read it
    for line in load_file_generator("test.txt"):
        print(line)
```

---

## 📝 Summary

1. **Check file exists**: Use `os.path.exists()` or `ls` command
2. **Use correct filename**: Check actual file name
3. **Use `__file__`**: For paths relative to script location
4. **Run from correct directory**: Or use absolute paths

**Your error was simply using the wrong filename!** 🎯

