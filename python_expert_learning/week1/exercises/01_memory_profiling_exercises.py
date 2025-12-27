"""
Week 1 - Exercise 1: Memory Profiling & Optimization

Complete these exercises to master memory profiling and optimization.
"""

import tracemalloc
import pandas as pd
import numpy as np
import os
from memory_profiler import profile
from sqlalchemy import Result

# ============================================================================
# Exercise 1: Memory Profiling
# ============================================================================
# Profile the memory usage of the following function and identify bottlenecks

def process_data_inefficient(data_list):
    """Inefficient data processing - find memory issues"""
    result = []
    for item in data_list:
        processed = item * 2
        result.append(processed)
        backup = result.copy()
    return result


# TODO: 
# 1. Profile this function using tracemalloc
# 2. Identify the memory bottleneck
# 3. Fix the memory issue
# 4. Measure the improvement



def exercise_1_profile():
    """Profile and optimize process_data_inefficient"""
    # Create test data
    data = list(range(100000))
    
    # Start profiling
    tracemalloc.start()
    
    # Run function
    result = process_data_inefficient(data)
    
    # Get memory stats
    current, peak = tracemalloc.get_traced_memory()
    print(f"Current: {current / 1024 / 1024:.2f} MB")
    print(f"Peak: {peak / 1024 / 1024:.2f} MB")
    
    tracemalloc.stop()
    
    # TODO: Fix the function and measure improvement
    pass


# ============================================================================
# Exercise 2: Convert to Generator
# ============================================================================
# Convert the following function to use a generator instead of a list

def load_file_to_list(file_path):
    """Loads entire file into memory - convert to generator"""
    with open(file_path, 'r') as f:
        lines = [line.strip() for line in f]
    return lines

# TODO: Convert to generator
def load_file_generator(file_path):
    """TODO: Implement as generator"""
    with open(file_path, 'r') as f:
        for line in f:
            yield line.strip()

#Test#
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
print(ROOT_DIR)
test_data = os.path.join(ROOT_DIR, 'test_data.txt')
for line in load_file_generator(test_data):
    print(line)


# ============================================================================
# Exercise 3: Chunked Processing
# ============================================================================
# Process a large CSV file in chunks instead of loading entirely

def process_csv_inefficient(file_path):
    """Loads entire CSV - optimize to use chunks"""
    df = pd.read_csv(file_path)  # Entire file in memory
    df['new_column'] = df['value'] * 2
    return df

# TODO: Implement chunked processing
def process_csv_chunked(file_path, chunk_size=10000):
    """TODO: Process CSV in chunks"""
    df = pd.read_csv(file_path, chunksize=chunk_size)
    for chunk in df:
        chunk['new_column'] = chunk['value'] * 2
    return df
# Test
large_file = os.path.join(ROOT_DIR, 'large_file.csv')
result = process_csv_chunked(large_file, chunk_size=10000)


# ============================================================================
# Exercise 4: Optimize NumPy Array Memory
# ============================================================================
# Optimize the following NumPy operations for memory

def create_features_inefficient(data):
    """Creates features inefficiently - optimize"""
    # Creates multiple copies
    features = []
    for value in data:
        feature_vector = np.array([
            value,
            value * 2,
            value ** 2,
            value + 10
        ], dtype=np.float64)  # Using float64
        features.append(feature_vector)
    
    return np.array(features)

# TODO: Optimize for memory
def create_features_optimized(data):
    """TODO: Optimize memory usage"""
    features = np.array([
        data,
        data * 2,
        data ** 2,
        data + 10
    ], dtype=np.float32)
    return features
    # Hints:
    # - Use float32 instead of float64
    # - Pre-allocate array if possible
    # - Avoid unnecessary copies

# Test
data = np.random.rand(100000)
features = create_features_optimized(data)
print(f"Memory usage: {features.nbytes / 1024 / 1024:.2f} MB")


# ============================================================================
# Exercise 5: Memory Leak Detection
# ============================================================================
# Find and fix the memory leak in the following code

class DataProcessor:
    def __init__(self):
        self.no_of_items = 10
        self.cache = {}
        self.processed_data = []
    
    def process(self, data):
        """Process data and store in cache - find memory leak"""
        result = process_function(data)
        self.cache[data.id] = result  # Memory leak!
        self.processed_data.append(result)  # Another leak!
        return result

# TODO: Fix memory leaks
class DataProcessorOptimized:
    """
    Fixes the memory leaks by making both the cache and history bounded.

    - cache: keep at most N items (evict oldest)
    - processed_data: keep only last N results
    """

    def __init__(self, max_items: int = 10):
        from collections import OrderedDict, deque

        self.no_of_items = int(max_items)
        self.cache = OrderedDict()          # key -> result (bounded)
        self.processed_data = deque(maxlen=self.no_of_items)  # bounded history

    def process(self, data):
        # NOTE: process_function is intentionally left as a placeholder in this exercise.
        result = process_function(data)

        key = data.id
        if key in self.cache:
            # refresh recency (optional LRU behavior)
            self.cache.move_to_end(key)
        self.cache[key] = result

        # Evict oldest items to keep cache bounded
        while len(self.cache) > self.no_of_items:
            self.cache.popitem(last=False)

        # Keep only last N results
        self.processed_data.append(result)
        return result


# ============================================================================
# Exercise 6: Pandas Memory Optimization
# ============================================================================
# Optimize the following Pandas DataFrame for memory

def create_dataframe_inefficient():
    """Creates inefficient DataFrame - optimize"""
    data = {
        'id': ['1', '2', '3'] * 1000000,  # Object dtype
        'category': ['A', 'B', 'C'] * 1000000,  # Object dtype
        'value': [1.0, 2.0, 3.0] * 1000000  # float64
    }
    df = pd.DataFrame(data)
    return df

# TODO: Optimize DataFrame memory
def create_dataframe_optimized():
    """TODO: Optimize DataFrame memory usage"""

    # Hints:
    # - Convert 'id' to int
    # - Convert 'category' to categorical
    # - Use float32 instead of float64
    # Build columns in the final dtypes up-front to avoid a big intermediate object DataFrame.
    repeats = 1_000_000
    df = pd.DataFrame(
        {
            "id": np.tile(np.array([1, 2, 3], dtype=np.int32), repeats),
            "category": pd.Categorical(np.tile(np.array(["A", "B", "C"]), repeats)),
            "value": np.tile(np.array([1.0, 2.0, 3.0], dtype=np.float32), repeats),
        }
    )
    return df

# Test
# df_inefficient = create_dataframe_inefficient()
# df_optimized = create_dataframe_optimized()
# print(f"Inefficient: {df_inefficient.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
# print(f"Optimized: {df_optimized.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")


# ============================================================================
# Exercise 7: Real-World ML Pipeline Optimization
# ============================================================================
# Optimize this ML feature engineering pipeline

def feature_engineering_pipeline_inefficient(data_path):
    """Inefficient ML pipeline - optimize"""
    # Load entire dataset
    df = pd.read_csv(data_path)
    
    # Create many features
    features = []
    for idx, row in df.iterrows():
        feature_dict = {
            'feature1': row['value'] * 2,
            'feature2': row['value'] ** 2,
            'feature3': row['value'] + row['other'],
            'feature4': row['value'] * row['other'],
            # ... many more features
        }
        features.append(feature_dict)
    
    # Convert to DataFrame

    dtypes = {'feature1': np.int32, 'feature2': np.int32, 'feature3': np.int32, 'feature4': np.int32}
    feature_df = pd.DataFrame(features, dtypes)

    
    return feature_df

# TODO: Optimize the entire pipeline
def feature_engineering_pipeline_optimized(data_path, chunk_size=10000):
    """TODO: Optimize the entire pipeline"""
    # Requirements:
    # - Process in chunks
    # - Use generators where possible
    # - Use appropriate dtypes
    # - Minimize memory copies
    processed_chunks: list[pd.DataFrame] = []

    # Read only needed columns, in chunks, with explicit dtypes.
    for chunk in pd.read_csv(
        data_path,
        chunksize=chunk_size,
        usecols=["value", "other"],
        dtype={"value": np.float32, "other": np.float32},
    ):
        v = chunk["value"].to_numpy(dtype=np.float32, copy=False)
        o = chunk["other"].to_numpy(dtype=np.float32, copy=False)

        # Vectorized feature computation (no iterrows / per-row dicts)
        out = pd.DataFrame(
            {
                "feature1": v * 2.0,
                "feature2": v * v,
                "feature3": v + o,
                "feature4": v * o,
            }
        ).astype(np.float32, copy=False)

        processed_chunks.append(out)

    # NOTE: concat keeps all output in memory; for huge data, write each chunk or yield.
    if not processed_chunks:
        return pd.DataFrame(columns=["feature1", "feature2", "feature3", "feature4"])
    return pd.concat(processed_chunks, ignore_index=True)


# ============================================================================
# Solutions Template
# ============================================================================
# After attempting the exercises, I'll provide solutions and explanations

if __name__ == "__main__":
    exercise_1_profile()
    print("Complete the exercises above!")
    print("Use memory profiling tools to verify your optimizations.")
    print("\nTips:")
    print("1. Always profile before optimizing")
    print("2. Use generators for large datasets")
    print("3. Process data in chunks")
    print("4. Use appropriate data types")
    print("5. Delete unused variables explicitly")

