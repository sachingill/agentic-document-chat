"""
Comparison: tracemalloc vs @profile

This script demonstrates both tools side-by-side.
"""

import tracemalloc
from memory_profiler import profile

def process_data_inefficient(data):
    """Function with memory issues"""
    result = []
    for item in data:
        result.append(item * 2)
        backup = result.copy()  # Memory leak - unnecessary copy!
    return result

# ============================================================================
# Method 1: tracemalloc (Built-in)
# ============================================================================

def test_with_tracemalloc():
    """Test using tracemalloc"""
    print("=" * 60)
    print("Method 1: tracemalloc (Built-in)")
    print("=" * 60)
    
    tracemalloc.start()
    
    data = list(range(100000))
    result = process_data_inefficient(data)
    
    current, peak = tracemalloc.get_traced_memory()
    print(f"Current memory: {current / 1024 / 1024:.2f} MB")
    print(f"Peak memory: {peak / 1024 / 1024:.2f} MB")
    
    # Get top memory allocations
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('lineno')
    
    print("\nTop 5 memory allocations:")
    for i, stat in enumerate(top_stats[:5], 1):
        print(f"  {i}. {stat}")
    
    tracemalloc.stop()
    
    print("\n✅ tracemalloc shows overall memory usage")
    print("   Run with: python script.py")


# ============================================================================
# Method 2: @profile (memory_profiler)
# ============================================================================

@profile  # ← Decorator for line-by-line profiling
def test_with_profile():
    """Test using @profile decorator"""
    print("\n" + "=" * 60)
    print("Method 2: @profile (memory_profiler)")
    print("=" * 60)
    print("(This will show line-by-line memory usage)")
    print("=" * 60)
    
    data = list(range(100000))
    result = process_data_inefficient(data)
    
    print("\n✅ @profile shows line-by-line memory usage")
    print("   Run with: python -m memory_profiler script.py")


# ============================================================================
# Method 3: Combined (Best of Both)
# ============================================================================

@profile
def process_data_with_profile(data):
    """Function with @profile decorator"""
    result = []
    for item in data:
        result.append(item * 2)
        backup = result.copy()  # Memory leak!
    return result

def test_combined():
    """Use both tracemalloc and @profile together"""
    print("\n" + "=" * 60)
    print("Method 3: Combined (tracemalloc + @profile)")
    print("=" * 60)
    
    # Overall tracking
    tracemalloc.start()
    
    data = list(range(100000))
    result = process_data_with_profile(data)  # @profile shows line-by-line
    
    # Overall stats
    current, peak = tracemalloc.get_traced_memory()
    print(f"\nOverall Memory (from tracemalloc):")
    print(f"  Current: {current / 1024 / 1024:.2f} MB")
    print(f"  Peak: {peak / 1024 / 1024:.2f} MB")
    
    tracemalloc.stop()
    
    print("\n✅ Combined: Line-by-line details + overall stats")
    print("   Run with: python -m memory_profiler script.py")


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Memory Profiling Comparison: tracemalloc vs @profile")
    print("=" * 60)
    
    # Test 1: tracemalloc only
    test_with_tracemalloc()
    
    # Test 2: @profile only
    # Note: @profile output only shows when run with: python -m memory_profiler
    test_with_profile()
    
    # Test 3: Combined
    test_combined()
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    print("1. tracemalloc: Overall memory, run with: python script.py")
    print("2. @profile: Line-by-line, run with: python -m memory_profiler script.py")
    print("3. Combined: Best of both worlds!")
    print("=" * 60)

