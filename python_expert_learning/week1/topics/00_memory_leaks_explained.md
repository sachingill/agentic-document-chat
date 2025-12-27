# Memory Leaks: How to Avoid Them

## 🎯 What is a Memory Leak?

A **memory leak** occurs when memory is allocated but never freed, causing memory usage to grow continuously.

---

## 🔍 Memory Leaks in DataProcessor Class

### Original Class (Has Memory Leaks)

```python
class DataProcessor:
    def __init__(self):
        self.cache = {}           # ← Grows forever
        self.processed_data = []  # ← Grows forever
    
    def process(self, data):
        result = process_function(data)
        self.cache[data.id] = result      # ← Memory leak #1: Never cleared
        self.processed_data.append(result) # ← Memory leak #2: Never cleared
        return result
```

### Problems:

1. **`self.cache` grows forever**
   - Every call to `process()` adds to cache
   - Cache is never cleared
   - Memory keeps growing

2. **`self.processed_data` grows forever**
   - Every result is stored
   - List never cleared
   - Memory keeps growing

---

## ✅ Fixed: DataProcessorOptimized

### Solution 1: Bounded Cache (LRU Cache)

```python
from functools import lru_cache
from collections import OrderedDict

class DataProcessorOptimized:
    def __init__(self, max_cache_size=100):
        # Use OrderedDict for LRU cache
        self.cache = OrderedDict()
        self.max_cache_size = max_cache_size
        # Don't store processed_data - not needed!
    
    def process(self, data):
        # Check cache first
        if data.id in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(data.id)
            return self.cache[data.id]
        
        # Process data
        result = process_function(data)
        
        # Add to cache
        self.cache[data.id] = result
        
        # Remove oldest if cache too large
        if len(self.cache) > self.max_cache_size:
            self.cache.popitem(last=False)  # Remove oldest
        
        return result
```

**How it avoids leaks:**
- ✅ Cache has maximum size
- ✅ Oldest entries removed automatically
- ✅ Memory usage bounded

---

### Solution 2: Don't Store Unnecessary Data

```python
class DataProcessorOptimized:
    def __init__(self, max_cache_size=100):
        self.cache = {}
        self.max_cache_size = max_cache_size
        # ✅ Removed processed_data - not needed!
    
    def process(self, data):
        # Check cache
        if data.id in self.cache:
            return self.cache[data.id]
        
        # Process
        result = process_function(data)
        
        # Add to cache (bounded)
        if len(self.cache) >= self.max_cache_size:
            # Remove random entry (or use LRU)
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        
        self.cache[data.id] = result
        return result
    
    def clear_cache(self):
        """Method to manually clear cache"""
        self.cache.clear()
```

**How it avoids leaks:**
- ✅ Removed `processed_data` (not needed)
- ✅ Bounded cache size
- ✅ Manual clear method

---

### Solution 3: Use Weak References

```python
import weakref

class DataProcessorOptimized:
    def __init__(self):
        # WeakValueDictionary - automatically removes when object deleted
        self.cache = weakref.WeakValueDictionary()
        # ✅ No processed_data - not needed
    
    def process(self, data):
        # Check cache
        if data.id in self.cache:
            return self.cache[data.id]
        
        # Process
        result = process_function(data)
        
        # Add to cache (weak reference)
        self.cache[data.id] = result
        return result
```

**How it avoids leaks:**
- ✅ Weak references - automatically cleaned up
- ✅ No manual cache management needed
- ✅ Memory freed when objects deleted

---

### Solution 4: Complete Solution (Recommended)

```python
from collections import OrderedDict

class DataProcessorOptimized:
    def __init__(self, max_cache_size=100):
        """
        Optimized data processor with bounded cache.
        
        Args:
            max_cache_size: Maximum number of items in cache (default: 100)
        """
        # LRU cache - automatically removes oldest when full
        self.cache = OrderedDict()
        self.max_cache_size = max_cache_size
        # ✅ Removed processed_data - not needed for processing
    
    def process(self, data):
        """
        Process data with caching.
        
        Args:
            data: Data object with .id attribute
            
        Returns:
            Processed result
        """
        # Check cache first (O(1) lookup)
        if data.id in self.cache:
            # Move to end (mark as recently used)
            self.cache.move_to_end(data.id)
            return self.cache[data.id]
        
        # Process data
        result = process_function(data)
        
        # Add to cache
        self.cache[data.id] = result
        
        # Remove oldest if cache too large
        if len(self.cache) > self.max_cache_size:
            self.cache.popitem(last=False)  # Remove oldest (FIFO)
        
        return result
    
    def clear_cache(self):
        """Clear the cache to free memory"""
        self.cache.clear()
    
    def get_cache_size(self):
        """Get current cache size"""
        return len(self.cache)
    
    def get_cache_info(self):
        """Get cache statistics"""
        return {
            'size': len(self.cache),
            'max_size': self.max_cache_size,
            'keys': list(self.cache.keys())
        }
```

**How it avoids leaks:**
- ✅ **Bounded cache**: Maximum size prevents unlimited growth
- ✅ **LRU eviction**: Oldest entries removed automatically
- ✅ **No unnecessary storage**: Removed `processed_data`
- ✅ **Manual cleanup**: `clear_cache()` method
- ✅ **Memory efficient**: Only stores what's needed

---

## 🔍 Memory Leak Patterns to Avoid

### Pattern 1: Unbounded Growth

```python
# ❌ BAD: Grows forever
self.cache = {}
self.cache[key] = value  # Never removed

# ✅ GOOD: Bounded
self.cache = OrderedDict()
if len(self.cache) > max_size:
    self.cache.popitem(last=False)
```

### Pattern 2: Storing Unnecessary Data

```python
# ❌ BAD: Stores everything
self.processed_data.append(result)  # Never cleared

# ✅ GOOD: Don't store if not needed
# Just return result, don't store
return result
```

### Pattern 3: Circular References

```python
# ❌ BAD: Circular reference
parent.children.append(child)
child.parent = parent  # Circular!

# ✅ GOOD: Weak reference
import weakref
child.parent = weakref.ref(parent)
```

### Pattern 4: Global Variables

```python
# ❌ BAD: Global grows forever
cache = {}
cache[key] = value  # Never cleared

# ✅ GOOD: Bounded or use LRU cache
from functools import lru_cache

@lru_cache(maxsize=100)
def process(data):
    return process_function(data)
```

---

## 📊 Memory Comparison

### Original DataProcessor

```python
processor = DataProcessor()
for i in range(1000000):
    processor.process(data)  # Memory keeps growing!
```

**Memory usage**: Grows linearly, never freed → **Memory leak!**

### Optimized DataProcessor

```python
processor = DataProcessorOptimized(max_cache_size=100)
for i in range(1000000):
    processor.process(data)  # Memory stays bounded!
```

**Memory usage**: Stays constant (bounded by cache size) → **No leak!**

---

## ✅ Key Principles to Avoid Memory Leaks

1. **Bound your data structures**
   - Set maximum sizes
   - Remove old entries

2. **Don't store unnecessary data**
   - Only store what you need
   - Delete when done

3. **Use appropriate data structures**
   - LRU cache for bounded caching
   - Weak references for temporary storage
   - Generators for large datasets

4. **Provide cleanup methods**
   - `clear_cache()` methods
   - Context managers for cleanup
   - Explicit deletion

5. **Monitor memory usage**
   - Use `tracemalloc` or `@profile`
   - Check for unbounded growth
   - Test with large datasets

---

## 🎯 Summary

**Memory leaks happen when:**
- Data structures grow forever
- Unnecessary data is stored
- No cleanup mechanisms

**Avoid leaks by:**
- Bounding data structures
- Removing unnecessary storage
- Using appropriate patterns (LRU, weak refs)
- Providing cleanup methods

**Your `DataProcessorOptimized` should:**
- ✅ Have bounded cache (max size)
- ✅ Remove old entries automatically
- ✅ Not store `processed_data` (unnecessary)
- ✅ Provide cleanup methods

---

**That's how to avoid memory leaks!** 🎯

