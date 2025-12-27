# Memory Profiler: `@profile` Decorator Explained

## 🎯 What is `@profile`?

`@profile` is a **decorator** from `memory_profiler` that tracks memory usage line-by-line in a function.

---

## 📝 How to Use `@profile`

### Step 1: Import and Decorate

```python
from memory_profiler import profile

@profile  # ← This decorator tracks memory usage
def my_function():
    result = []
    for i in range(100000):
        result.append(i * 2)
    return result
```

### Step 2: Run with `memory_profiler`

**Important**: You must run the file using `memory_profiler`, NOT regular Python!

```bash
# ❌ This WON'T work (no output)
python my_file.py

# ✅ This WORKS (shows memory usage)
python -m memory_profiler my_file.py
```

---

## 🔍 Example: With and Without `@profile`

### Without `@profile` (No Memory Tracking)

```python
from memory_profiler import profile

def process_data(data):
    result = []
    for item in data:
        result.append(item * 2)
    return result

if __name__ == "__main__":
    data = list(range(100000))
    result = process_data(data)
```

**Running**: `python -m memory_profiler script.py`
**Output**: Nothing (no memory profiling)

---

### With `@profile` (Memory Tracking)

```python
from memory_profiler import profile

@profile  # ← Add this decorator
def process_data(data):
    result = []
    for item in data:
        result.append(item * 2)
    return result

if __name__ == "__main__":
    data = list(range(100000))
    result = process_data(data)
```

**Running**: `python -m memory_profiler script.py`
**Output**:
```
Line #    Mem usage    Increment  Line Contents
================================================
     3     45.2 MiB      0.0 MiB   @profile
     4     45.2 MiB      0.0 MiB   def process_data(data):
     5     45.2 MiB      0.0 MiB       result = []
     6    125.8 MiB     80.6 MiB       for item in data:
     7    125.8 MiB      0.0 MiB           result.append(item * 2)
     8    125.8 MiB      0.0 MiB       return result
```

**Shows**: Memory usage at each line!

---

## 🎯 Why You Might Not See It Working

### Problem 1: Running with Regular Python

```bash
# ❌ This doesn't work
python memory_profile.py

# ✅ This works
python -m memory_profiler memory_profile.py
```

### Problem 2: Function Not Called

```python
from memory_profiler import profile

@profile
def my_function():  # ← Decorated but never called
    pass

if __name__ == "__main__":
    # my_function()  # ← Not called!
    pass
```

**Fix**: Call the function!

```python
if __name__ == "__main__":
    my_function()  # ← Now it will be profiled
```

### Problem 3: Decorator Not Applied

```python
from memory_profiler import profile

# ❌ Imported but not used
def my_function():
    pass

# ✅ Use it as decorator
@profile
def my_function():
    pass
```

---

## 📝 Complete Working Example

### File: `memory_profile_example.py`

```python
from memory_profiler import profile

@profile  # ← Decorator tracks this function
def process_data_inefficient(data_list):
    """Inefficient function - we'll see memory usage"""
    result = []
    for item in data_list:
        processed = item * 2
        result.append(processed)
        # Memory leak: creating unnecessary copy
        backup = result.copy()  # ← This will show high memory usage!
    return result

@profile  # ← Can profile multiple functions
def process_data_efficient(data_list):
    """Efficient function - compare memory usage"""
    result = []
    for item in data_list:
        processed = item * 2
        result.append(processed)
        # No unnecessary copy
    return result

if __name__ == "__main__":
    data = list(range(100000))
    
    print("=" * 60)
    print("Inefficient Version:")
    print("=" * 60)
    result1 = process_data_inefficient(data)
    
    print("\n" + "=" * 60)
    print("Efficient Version:")
    print("=" * 60)
    result2 = process_data_efficient(data)
```

### Run It:

```bash
python -m memory_profiler memory_profile_example.py
```

### Output:

```
============================================================
Inefficient Version:
============================================================
Line #    Mem usage    Increment  Line Contents
================================================
     4     45.2 MiB      0.0 MiB   @profile
     5     45.2 MiB      0.0 MiB   def process_data_inefficient(data_list):
     6     45.2 MiB      0.0 MiB       result = []
     7    125.8 MiB     80.6 MiB       for item in data_list:
     8    125.8 MiB      0.0 MiB           processed = item * 2
     9    125.8 MiB      0.0 MiB           result.append(processed)
    10    250.4 MiB    124.6 MiB           backup = result.copy()  ← HIGH MEMORY!
    11    250.4 MiB      0.0 MiB       return result

============================================================
Efficient Version:
============================================================
Line #    Mem usage    Increment  Line Contents
================================================
    13     45.2 MiB      0.0 MiB   @profile
    14     45.2 MiB      0.0 MiB   def process_data_efficient(data_list):
    15     45.2 MiB      0.0 MiB       result = []
    16    125.8 MiB     80.6 MiB       for item in data_list:
    17    125.8 MiB      0.0 MiB           processed = item * 2
    18    125.8 MiB      0.0 MiB           result.append(processed)
    19    125.8 MiB      0.0 MiB       return result
```

**See the difference?** Line 10 shows high memory usage from the unnecessary copy!

---

## 🔧 Fixing Your Code

Looking at your `memory_profile.py`:

```python
from memory_profiler import profile

def process_data_inefficient(data_list):
    # ... your code ...

def exercise_1_profile():
    # ... your code ...

if __name__ == "__main__":
    exercise_1_profile()
```

### To Use `@profile`:

```python
from memory_profiler import profile

@profile  # ← Add this to profile the function
def process_data_inefficient(data_list):
    """Inefficient data processing - find memory issues"""
    result = []
    for item in data_list:
        processed = item * 2
        result.append(processed)
        backup = result.copy()  # Memory leak!
    return result

@profile  # ← Profile this too
def exercise_1_profile():
    data = list(range(100000))
    tracemalloc.start()
    result = process_data_inefficient(data)
    current, peak = tracemalloc.get_traced_memory()
    print(f"Current: {current / 1024 / 1024:.2f} MB")
    print(f"Peak: {peak / 1024 / 1024:.2f} MB")
    tracemalloc.stop()
    return result

if __name__ == "__main__":
    exercise_1_profile()
```

### Run It:

```bash
python -m memory_profiler memory_profile.py
```

**Now you'll see line-by-line memory usage!**

---

## 🎯 Key Points

1. **`@profile` is a decorator** - Put it above the function
2. **Must run with `python -m memory_profiler`** - Not regular Python
3. **Function must be called** - Decorator only works when function executes
4. **Shows line-by-line memory** - See exactly where memory is used

---

## 💡 Alternative: Use `tracemalloc` (No Decorator Needed)

If you don't want to use the decorator, use `tracemalloc` (built-in):

```python
import tracemalloc

def process_data(data):
    result = []
    for item in data:
        result.append(item * 2)
    return result

if __name__ == "__main__":
    tracemalloc.start()
    data = list(range(100000))
    result = process_data(data)
    current, peak = tracemalloc.get_traced_memory()
    print(f"Current: {current / 1024 / 1024:.2f} MB")
    print(f"Peak: {peak / 1024 / 1024:.2f} MB")
    tracemalloc.stop()
```

**No decorator needed!** Works with regular `python script.py`

---

## ✅ Summary

- **`@profile`**: Decorator for line-by-line memory profiling
- **Must run**: `python -m memory_profiler script.py`
- **Function must be called**: Decorator only works when function executes
- **Alternative**: Use `tracemalloc` for simpler memory tracking

**That's why you might not see `profile` being used - it needs to be run with `memory_profiler` module!** 🎯

