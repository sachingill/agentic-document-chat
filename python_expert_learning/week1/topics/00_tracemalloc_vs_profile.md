# tracemalloc vs @profile: Complete Comparison

## 🎯 Quick Answer

| Feature | `tracemalloc` | `@profile` (memory_profiler) |
|---------|---------------|------------------------------|
| **Built-in** | ✅ Yes (Python 3.4+) | ❌ Need to install |
| **Line-by-line** | ❌ No | ✅ Yes |
| **Overall memory** | ✅ Yes | ✅ Yes |
| **Run command** | `python script.py` | `python -m memory_profiler script.py` |
| **Best for** | Quick checks, overall memory | Detailed line-by-line analysis |

---

## 📊 Detailed Comparison

### 1. tracemalloc (Built-in)

**What it is:**
- Built-in Python module (Python 3.4+)
- Tracks memory allocations
- Shows overall memory usage
- Can show top memory allocations

**Pros:**
- ✅ No installation needed
- ✅ Works with regular `python script.py`
- ✅ Good for overall memory tracking
- ✅ Can identify memory leaks
- ✅ Shows top memory allocations

**Cons:**
- ❌ No line-by-line breakdown
- ❌ Less detailed than `@profile`

---

### 2. @profile (memory_profiler)

**What it is:**
- External package (need to install)
- Decorator for functions
- Shows line-by-line memory usage
- Very detailed analysis

**Pros:**
- ✅ Line-by-line memory usage
- ✅ Shows exactly where memory is used
- ✅ Great for detailed analysis
- ✅ Shows memory increment per line

**Cons:**
- ❌ Need to install: `pip install memory-profiler`
- ❌ Must run with `python -m memory_profiler script.py`
- ❌ Only works on decorated functions
- ❌ Slower execution

---

## 📝 Usage Examples

### tracemalloc Example

```python
import tracemalloc

def process_data(data):
    result = []
    for item in data:
        result.append(item * 2)
        backup = result.copy()  # Memory leak!
    return result

if __name__ == "__main__":
    # Start tracking
    tracemalloc.start()
    
    data = list(range(100000))
    result = process_data(data)
    
    # Get current and peak memory
    current, peak = tracemalloc.get_traced_memory()
    print(f"Current memory: {current / 1024 / 1024:.2f} MB")
    print(f"Peak memory: {peak / 1024 / 1024:.2f} MB")
    
    # Get top memory allocations
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('lineno')
    
    print("\nTop 10 memory allocations:")
    for stat in top_stats[:10]:
        print(stat)
    
    tracemalloc.stop()
```

**Output:**
```
Current memory: 45.23 MB
Peak memory: 250.45 MB

Top 10 memory allocations:
/path/to/script.py:10: size=125.2 MiB, count=100000
/path/to/script.py:11: size=125.2 MiB, count=100000
```

**Run with:** `python script.py` ✅

---

### @profile Example

```python
from memory_profiler import profile

@profile  # ← Decorator
def process_data(data):
    result = []
    for item in data:
        result.append(item * 2)
        backup = result.copy()  # Memory leak!
    return result

if __name__ == "__main__":
    data = list(range(100000))
    result = process_data(data)
```

**Run with:** `python -m memory_profiler script.py` ✅

**Output:**
```
Line #    Mem usage    Increment  Line Contents
================================================
     4     45.2 MiB      0.0 MiB   @profile
     5     45.2 MiB      0.0 MiB   def process_data(data):
     6     45.2 MiB      0.0 MiB       result = []
     7    125.8 MiB     80.6 MiB       for item in data:
     8    125.8 MiB      0.0 MiB           result.append(item * 2)
     9    250.4 MiB    124.6 MiB           backup = result.copy()  ← HIGH!
    10    250.4 MiB      0.0 MiB       return result
```

**Shows line-by-line memory usage!**

---

## 🔍 Side-by-Side Comparison

### Example: Finding Memory Leak

**Code with memory leak:**
```python
def process_data(data):
    result = []
    for item in data:
        result.append(item * 2)
        backup = result.copy()  # Memory leak - unnecessary copy!
    return result
```

### Using tracemalloc

```python
import tracemalloc

tracemalloc.start()
data = list(range(100000))
result = process_data(data)
current, peak = tracemalloc.get_traced_memory()
print(f"Peak: {peak / 1024 / 1024:.2f} MB")
tracemalloc.stop()
```

**Output:**
```
Peak: 250.45 MB
```

**What you learn:**
- ✅ Overall memory usage
- ✅ Peak memory
- ❌ Not which line caused it

---

### Using @profile

```python
from memory_profiler import profile

@profile
def process_data(data):
    result = []
    for item in data:
        result.append(item * 2)
        backup = result.copy()  # Memory leak!
    return result

if __name__ == "__main__":
    data = list(range(100000))
    result = process_data(data)
```

**Run:** `python -m memory_profiler script.py`

**Output:**
```
Line #    Mem usage    Increment  Line Contents
================================================
     4     45.2 MiB      0.0 MiB   @profile
     5     45.2 MiB      0.0 MiB   def process_data(data):
     6     45.2 MiB      0.0 MiB       result = []
     7    125.8 MiB     80.6 MiB       for item in data:
     8    125.8 MiB      0.0 MiB           result.append(item * 2)
     9    250.4 MiB    124.6 MiB           backup = result.copy()  ← FOUND IT!
    10    250.4 MiB      0.0 MiB       return result
```

**What you learn:**
- ✅ Line-by-line memory usage
- ✅ Exact line causing high memory (line 9)
- ✅ Memory increment per line
- ✅ Can see the problem immediately

---

## 🎯 When to Use Which?

### Use `tracemalloc` when:
- ✅ Quick memory check
- ✅ Overall memory usage
- ✅ Finding memory leaks (general)
- ✅ Production code (no decorators needed)
- ✅ Don't want to install packages
- ✅ Need to track memory over time

### Use `@profile` when:
- ✅ Need line-by-line details
- ✅ Finding exact memory bottlenecks
- ✅ Debugging specific functions
- ✅ Development/debugging
- ✅ Can install packages
- ✅ Want detailed analysis

---

## 💡 Combined Approach (Best of Both)

You can use both together:

```python
import tracemalloc
from memory_profiler import profile

@profile  # Line-by-line for this function
def process_data(data):
    result = []
    for item in data:
        result.append(item * 2)
        backup = result.copy()
    return result

if __name__ == "__main__":
    # Overall memory tracking
    tracemalloc.start()
    
    data = list(range(100000))
    result = process_data(data)  # @profile shows line-by-line
    
    # Overall memory stats
    current, peak = tracemalloc.get_traced_memory()
    print(f"\nOverall Memory:")
    print(f"  Current: {current / 1024 / 1024:.2f} MB")
    print(f"  Peak: {peak / 1024 / 1024:.2f} MB")
    
    tracemalloc.stop()
```

**Run:** `python -m memory_profiler script.py`

**You get:**
- Line-by-line details from `@profile`
- Overall memory stats from `tracemalloc`

---

## 📊 Performance Comparison

### tracemalloc
- **Speed**: Fast (minimal overhead)
- **Overhead**: ~5-10% slower
- **Best for**: Production monitoring

### @profile
- **Speed**: Slower (detailed tracking)
- **Overhead**: ~50-100% slower
- **Best for**: Development/debugging

---

## 🔧 Installation

### tracemalloc
```bash
# ✅ Already installed (Python 3.4+)
# No installation needed!
```

### @profile (memory_profiler)
```bash
# ❌ Need to install
pip install memory-profiler
```

---

## 📝 Quick Reference

### tracemalloc Quick Start

```python
import tracemalloc

tracemalloc.start()
# Your code here
current, peak = tracemalloc.get_traced_memory()
print(f"Peak: {peak / 1024 / 1024:.2f} MB")
tracemalloc.stop()
```

### @profile Quick Start

```python
from memory_profiler import profile

@profile
def my_function():
    # Your code here
    pass

if __name__ == "__main__":
    my_function()
```

**Run:** `python -m memory_profiler script.py`

---

## ✅ Summary

| Aspect | tracemalloc | @profile |
|--------|-------------|----------|
| **Installation** | Built-in | Need to install |
| **Run command** | `python script.py` | `python -m memory_profiler script.py` |
| **Detail level** | Overall | Line-by-line |
| **Speed** | Fast | Slower |
| **Best for** | Quick checks, production | Detailed debugging |
| **Shows** | Total memory, peak | Memory per line |

**Recommendation:**
- **Development**: Use `@profile` for detailed analysis
- **Production**: Use `tracemalloc` for monitoring
- **Both**: Use together for comprehensive analysis

---

**Both are useful - choose based on your needs!** 🎯

