# Using `__file__` for File Paths - Best Practice

## 🎯 The Problem

When you run a Python script, file paths are **relative to where you run the command**, not where the script is located.

### Example Problem

```python
# script.py (located in /path/to/scripts/)
with open("data.txt", 'r') as f:
    pass
```

```bash
# Run from different directory
cd /home/user/
python /path/to/scripts/script.py

# Python looks for: /home/user/data.txt  ❌ Wrong!
# But file is at: /path/to/scripts/data.txt  ✅ Correct
```

---

## ✅ Solution: Use `__file__`

`__file__` is a special variable that contains the path to the current script.

### How to Use It

```python
import os

# Get the directory where THIS script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Now files are relative to script location
file_path = os.path.join(script_dir, "data.txt")

with open(file_path, 'r') as f:
    pass
```

**Now it works from any directory!**

---

## 📝 Step-by-Step Explanation

### Step 1: `__file__`
```python
print(__file__)
# Output: /path/to/script.py (or script.py if relative)
```

### Step 2: `os.path.abspath(__file__)`
```python
print(os.path.abspath(__file__))
# Output: /full/absolute/path/to/script.py
```

### Step 3: `os.path.dirname(...)`
```python
script_dir = os.path.dirname(os.path.abspath(__file__))
print(script_dir)
# Output: /full/absolute/path/to
```

### Step 4: `os.path.join(...)`
```python
file_path = os.path.join(script_dir, "data.txt")
print(file_path)
# Output: /full/absolute/path/to/data.txt
```

---

## 🎯 Complete Example

### Before (Doesn't Work from Different Directory)

```python
def load_file_generator(file_path):
    with open(file_path, 'r') as f:  # ❌ Looks in current directory
        for line in f:
            yield line.strip()

if __name__ == "__main__":
    # ❌ Only works if run from exercises/ directory
    for line in load_file_generator("01_memory_profiling_exercises.py"):
        print(line)
```

### After (Works from Any Directory)

```python
import os

def load_file_generator(file_path):
    with open(file_path, 'r') as f:
        for line in f:
            yield line.strip()

if __name__ == "__main__":
    # ✅ Get script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # ✅ Build path relative to script location
    file_path = os.path.join(script_dir, "01_memory_profiling_exercises.py")
    
    # ✅ Now works from any directory!
    for line in load_file_generator(file_path):
        print(line)
```

---

## 💡 Helper Function

Create a helper function for convenience:

```python
import os

def get_script_dir():
    """Get the directory where the current script is located"""
    return os.path.dirname(os.path.abspath(__file__))

def get_script_path(filename):
    """Get path to a file in the same directory as the script"""
    return os.path.join(get_script_dir(), filename)

# Usage
file_path = get_script_path("data.txt")
with open(file_path, 'r') as f:
    pass
```

---

## 🔍 Check if File Exists

Always check if file exists before opening:

```python
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, "data.txt")

if os.path.exists(file_path):
    with open(file_path, 'r') as f:
        pass
else:
    print(f"File not found: {file_path}")
```

---

## ✅ Best Practices

1. **Always use `__file__`** for files in the same directory as script
2. **Use `os.path.join()`** to build paths (works on all OS)
3. **Check if file exists** before opening
4. **Use absolute paths** when needed
5. **Document path assumptions** in comments

---

## 🎯 Quick Reference

```python
import os

# Get script directory
script_dir = os.path.dirname(os.path.abspath(__file__))

# Build file path
file_path = os.path.join(script_dir, "filename.txt")

# Check if exists
if os.path.exists(file_path):
    # Use file
    pass
```

**This is the professional way to handle file paths!** 🎯

