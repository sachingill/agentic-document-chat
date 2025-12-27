"""
Test script to demonstrate memory leak fix in DataProcessorOptimized
"""

import tracemalloc
from collections import OrderedDict

# Simulate the original class with memory leak
class DataProcessor:
    """Original class with memory leaks"""
    def __init__(self):
        self.cache = {}           # ← Grows forever
        self.processed_data = []  # ← Grows forever
    
    def process(self, data):
        result = data * 2  # Simple processing
        self.cache[data] = result      # Memory leak #1
        self.processed_data.append(result)  # Memory leak #2
        return result

# Optimized class without memory leaks
class DataProcessorOptimized:
    """Optimized class that avoids memory leaks"""
    def __init__(self, max_cache_size=100):
        self.cache = OrderedDict()  # LRU cache
        self.max_cache_size = max_cache_size
        # ✅ Removed processed_data - not needed!
    
    def process(self, data):
        # Check cache
        if data in self.cache:
            self.cache.move_to_end(data)  # LRU
            return self.cache[data]
        
        # Process
        result = data * 2
        
        # Add to cache
        self.cache[data] = result
        
        # Remove oldest if cache too large (prevents leak!)
        if len(self.cache) > self.max_cache_size:
            self.cache.popitem(last=False)
        
        return result
    
    def clear_cache(self):
        """Clear cache to free memory"""
        self.cache.clear()

def test_memory_leak():
    """Test original class - shows memory leak"""
    print("=" * 60)
    print("Test 1: Original DataProcessor (Has Memory Leak)")
    print("=" * 60)
    
    tracemalloc.start()
    
    processor = DataProcessor()
    for i in range(100000):
        processor.process(i)
    
    current, peak = tracemalloc.get_traced_memory()
    print(f"Cache size: {len(processor.cache):,}")
    print(f"Processed data size: {len(processor.processed_data):,}")
    print(f"Peak memory: {peak / 1024 / 1024:.2f} MB")
    
    tracemalloc.stop()
    
    print("\n❌ Memory leak: Cache and processed_data grow forever!")

def test_optimized():
    """Test optimized class - no memory leak"""
    print("\n" + "=" * 60)
    print("Test 2: DataProcessorOptimized (No Memory Leak)")
    print("=" * 60)
    
    tracemalloc.start()
    
    processor = DataProcessorOptimized(max_cache_size=100)
    for i in range(100000):
        processor.process(i)
    
    current, peak = tracemalloc.get_traced_memory()
    print(f"Cache size: {processor.get_cache_size()}")
    print(f"Max cache size: {processor.max_cache_size}")
    print(f"Peak memory: {peak / 1024 / 1024:.2f} MB")
    
    tracemalloc.stop()
    
    print("\n✅ No memory leak: Cache is bounded!")

if __name__ == "__main__":
    test_memory_leak()
    test_optimized()
    
    print("\n" + "=" * 60)
    print("Key Differences:")
    print("=" * 60)
    print("Original:")
    print("  - Cache grows forever (100,000 entries)")
    print("  - processed_data grows forever (100,000 entries)")
    print("  - Memory leak!")
    print()
    print("Optimized:")
    print("  - Cache bounded (max 100 entries)")
    print("  - No processed_data storage")
    print("  - No memory leak!")
    print("=" * 60)

