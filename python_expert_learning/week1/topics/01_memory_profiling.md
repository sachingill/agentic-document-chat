# Topic 1: Memory Profiling & Optimization for AI Systems

## 🎯 Learning Objectives
- Master memory profiling tools (memory_profiler, tracemalloc)
- Understand memory usage in ML systems
- Optimize memory consumption for large datasets
- Detect and fix memory leaks
- Write memory-efficient code

---

## 1. Why Memory Matters in AI/ML Systems

### The Problem
- **Large datasets**: ML systems process GBs/TBs of data
- **Model inference**: Models can consume significant memory
- **Feature engineering**: Creating features multiplies memory usage
- **Production constraints**: Limited memory in production environments

### Real-World Impact
- **Out of Memory (OOM) errors**: System crashes
- **Slow performance**: Memory pressure causes swapping
- **Cost**: More memory = higher cloud costs
- **Scalability**: Memory limits horizontal scaling

---

## 2. Memory Profiling Tools

### Tool 1: `memory_profiler`

**Installation:**
```bash
pip install memory-profiler
```

**Basic Usage:**
```python
from memory_profiler import profile

@profile
def process_data(data):
    result = []
    for item in data:
        result.append(item * 2)
    return result

# Run with: python -m memory_profiler script.py
```

**Output:**
```
Line #    Mem usage    Increment  Line Contents
================================================
     3     45.2 MiB      0.0 MiB   def process_data(data):
     4     45.2 MiB      0.0 MiB       result = []
     5    125.8 MiB     80.6 MiB       for item in data:
     6    125.8 MiB      0.0 MiB           result.append(item * 2)
     7    125.8 MiB      0.0 MiB       return result
```

### Tool 2: `tracemalloc` (Built-in)

**Usage:**
```python
import tracemalloc

tracemalloc.start()

# Your code here
data = process_large_dataset()

current, peak = tracemalloc.get_traced_memory()
print(f"Current memory usage: {current / 1024 / 1024:.2f} MB")
print(f"Peak memory usage: {peak / 1024 / 1024:.2f} MB")

snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

print("\nTop 10 memory allocations:")
for stat in top_stats[:10]:
    print(stat)
```

### Tool 3: `pympler`

**Installation:**
```bash
pip install pympler
```

**Usage:**
```python
from pympler import tracker, muppy, summary

tr = tracker.SummaryTracker()

# Your code here
process_data()

tr.print_diff()  # Shows memory differences
```

---

## 3. Memory Optimization Techniques

### Technique 1: Use Generators Instead of Lists

**❌ Memory-Intensive:**
```python
def load_all_data(file_path):
    """Loads entire file into memory"""
    with open(file_path) as f:
        return [line.strip() for line in f]  # Creates list in memory

# Problem: Entire file in memory
data = load_all_data('large_file.txt')  # Could be GBs
```

**✅ Memory-Efficient:**
```python
def load_data_generator(file_path):
    """Generator - processes one line at a time"""
    with open(file_path) as f:
        for line in f:
            yield line.strip()  # Yields one item at a time

# Memory efficient: Only one line in memory at a time
for line in load_data_generator('large_file.txt'):
    process(line)
```

**Memory Savings:**
- List approach: O(n) memory (entire file)
- Generator approach: O(1) memory (one line)

### Technique 2: Process Data in Chunks

**❌ Memory-Intensive:**
```python
import pandas as pd

# Load entire dataset
df = pd.read_csv('large_dataset.csv')  # Could be GBs
processed = df.apply(process_function)
```

**✅ Memory-Efficient:**
```python
import pandas as pd

# Process in chunks
chunk_size = 10000
results = []

for chunk in pd.read_csv('large_dataset.csv', chunksize=chunk_size):
    processed_chunk = chunk.apply(process_function)
    results.append(processed_chunk)
    # Chunk is garbage collected after processing

final_df = pd.concat(results)
```

**Memory Savings:**
- Full load: Entire dataset in memory
- Chunked: Only chunk_size rows in memory

### Technique 3: Delete Unused Variables

**❌ Memory Leak:**
```python
def process_data():
    raw_data = load_large_dataset()  # 5GB
    processed = process(raw_data)
    # raw_data still in memory!
    return processed
```

**✅ Explicit Cleanup:**
```python
def process_data():
    raw_data = load_large_dataset()  # 5GB
    processed = process(raw_data)
    del raw_data  # Explicitly delete
    import gc
    gc.collect()  # Force garbage collection
    return processed
```

### Technique 4: Use Appropriate Data Types

**❌ Memory Waste:**
```python
import numpy as np

# Default float64 (8 bytes per element)
data = np.array([1, 2, 3, 4, 5], dtype=np.float64)  # 40 bytes
```

**✅ Memory Efficient:**
```python
import numpy as np

# Use float32 (4 bytes per element) if precision allows
data = np.array([1, 2, 3, 4, 5], dtype=np.float32)  # 20 bytes (50% savings)

# Or int8 for small integers
data = np.array([1, 2, 3, 4, 5], dtype=np.int8)  # 5 bytes (87.5% savings)
```

**Memory Savings:**
- float64 → float32: 50% reduction
- float64 → int8: 87.5% reduction (when applicable)

### Technique 5: Use Generators for Feature Engineering

**❌ Memory-Intensive Feature Engineering:**
```python
def create_features(data):
    features = []
    for row in data:
        feature_vector = [
            row['value'] * 2,
            row['value'] ** 2,
            row['value'] + row['other'],
            # ... many more features
        ]
        features.append(feature_vector)  # All features in memory
    return features
```

**✅ Memory-Efficient:**
```python
def create_features_generator(data):
    """Generator for feature engineering"""
    for row in data:
        feature_vector = [
            row['value'] * 2,
            row['value'] ** 2,
            row['value'] + row['other'],
            # ... many more features
        ]
        yield feature_vector  # One feature vector at a time

# Process features one at a time
for features in create_features_generator(data):
    model.predict(features)
```

---

## 4. NumPy/Pandas Memory Optimization

### NumPy Optimization

**Use views instead of copies:**
```python
import numpy as np

# ❌ Creates copy (doubles memory)
arr = np.array([1, 2, 3, 4, 5])
subset = arr[1:4].copy()  # Copy

# ✅ Creates view (no extra memory)
arr = np.array([1, 2, 3, 4, 5])
subset = arr[1:4]  # View (shares memory)
```

**Use in-place operations:**
```python
# ❌ Creates new array
arr = arr * 2  # New array created

# ✅ In-place operation
arr *= 2  # Modifies existing array
```

### Pandas Optimization

**Use appropriate dtypes:**
```python
import pandas as pd

# ❌ Object dtype (inefficient)
df = pd.DataFrame({'id': ['1', '2', '3']})  # Object dtype

# ✅ Categorical or numeric
df = pd.DataFrame({'id': [1, 2, 3]})  # int64
# Or for strings with few unique values:
df['category'] = df['category'].astype('category')  # Much more efficient
```

**Memory usage comparison:**
```python
df = pd.DataFrame({'category': ['A', 'B', 'A', 'B'] * 1000000})

# Object dtype
print(df.memory_usage(deep=True))  # ~8MB

# Categorical dtype
df['category'] = df['category'].astype('category')
print(df.memory_usage(deep=True))  # ~1MB (87.5% reduction!)
```

---

## 5. Detecting Memory Leaks

### Common Memory Leak Patterns

**Pattern 1: Circular References**
```python
class Node:
    def __init__(self, value):
        self.value = value
        self.parent = None
        self.children = []

# Circular reference
parent = Node(1)
child = Node(2)
parent.children.append(child)
child.parent = parent  # Circular reference!

# Solution: Use weak references
import weakref
child.parent = weakref.ref(parent)
```

**Pattern 2: Global Variables**
```python
# ❌ Global variable accumulates data
cache = {}

def process_data(data):
    cache[data.id] = data  # Never cleared!
    return process(data)

# ✅ Use bounded cache
from functools import lru_cache

@lru_cache(maxsize=100)
def process_data(data):
    return process(data)
```

**Pattern 3: Event Listeners**
```python
# ❌ Listeners not removed
class EventHandler:
    def __init__(self):
        self.listeners = []
    
    def add_listener(self, listener):
        self.listeners.append(listener)  # Never removed!

# ✅ Remove listeners when done
def cleanup(self):
    self.listeners.clear()
```

---

## 6. Practical Example: Optimizing ML Data Pipeline

### Before Optimization

```python
import pandas as pd
import numpy as np

def load_and_process_data(file_path):
    # Load entire dataset
    df = pd.read_csv(file_path)  # 5GB in memory
    
    # Create many features
    features = []
    for idx, row in df.iterrows():
        feature_vector = create_features(row)  # Creates list
        features.append(feature_vector)
    
    # Convert to numpy array
    X = np.array(features)  # Another 5GB in memory
    
    # Process
    processed = process_features(X)
    
    return processed
```

**Memory Usage:** ~10GB+ (dataset + features + processing)

### After Optimization

```python
import pandas as pd
import numpy as np

def load_and_process_data_optimized(file_path):
    # Process in chunks
    chunk_size = 10000
    results = []
    
    for chunk in pd.read_csv(file_path, chunksize=chunk_size):
        # Process chunk
        features = []
        for idx, row in chunk.iterrows():
            feature_vector = create_features(row)
            features.append(feature_vector)
        
        X_chunk = np.array(features, dtype=np.float32)  # Use float32
        processed_chunk = process_features(X_chunk)
        results.append(processed_chunk)
        
        # Chunk is garbage collected
        del chunk, features, X_chunk
    
    # Combine results
    return np.concatenate(results)
```

**Memory Usage:** ~100MB (only chunk in memory)

**Improvement:** 100x memory reduction!

---

## 7. Best Practices

### ✅ Do's
- Use generators for large datasets
- Process data in chunks
- Use appropriate data types (float32 vs float64)
- Delete unused variables explicitly
- Use views instead of copies when possible
- Profile memory usage regularly
- Use categorical dtypes in Pandas

### ❌ Don'ts
- Don't load entire datasets into memory
- Don't create unnecessary copies
- Don't use object dtypes when numeric works
- Don't accumulate data in global variables
- Don't ignore memory warnings
- Don't use float64 when float32 is sufficient

---

## 🎯 Key Takeaways

1. **Profile First**: Always profile before optimizing
2. **Generators**: Use generators for large datasets
3. **Chunking**: Process data in chunks
4. **Data Types**: Use appropriate dtypes (float32, categorical)
5. **Cleanup**: Explicitly delete unused variables
6. **Views**: Use views instead of copies when possible

---

## 📝 Practice Exercises

See `exercises/01_memory_profiling_exercises.py`

---

## 🔗 Next Topic
[Topic 2: Performance Optimization with Profiling](./02_performance_profiling.md)

