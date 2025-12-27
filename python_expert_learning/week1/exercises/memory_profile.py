import tracemalloc
import os
from memory_profiler import profile
import pandas as pd
import numpy as np

def  process_data_inefficient(data_list):
    """Inefficient data processing - find memory issues"""
    result = []
    for item in data_list:
        prcoessed = item * 2
        result.append(prcoessed)
        backup = result.copy()

    return result


def exercise_1_profile():
    data = list(range(100000))

    tracemalloc.start()

    result = process_data_inefficient(data)

    current, peak = tracemalloc.get_traced_memory()
    print(f"Current: {current / 1024 / 1024:.2f} MB")
    print(f"Peak: {peak / 1024 / 1024:.2f} MB")

    tracemalloc.stop()

    return result

def load_file_to_list(file_path):
    """Loads entire file into memory - convert to generator"""
    with open(file_path, 'r') as f:
        lines = [line.strip() for line in f]
    return lines

# TODO: Convert to generator
def load_file_generator(file_path):
    with open(file_path, 'r') as f:
        for line in f:
            print(line)
            yield line.strip()

def process_csv_inefficient(file_path):
    """Loads entire CSV - optimize to use chunks""" 
    df = pd.read_csv(file_path)
    df['new_column'] = df['value'] * 2
    return df

# TODO: Implement chunked processing
def process_csv_chunked(file_path, chunk_size=10000):
    """Process CSV in chunks - memory efficient"""
    results = []
    
    # Read CSV in chunks
    for chunk in pd.read_csv(file_path, chunksize=chunk_size):
        # Process chunk
        chunk['new_column'] = chunk['value'] * 2
        results.append(chunk)
        # Chunk is automatically garbage collected after loop iteration
    
    # Combine all chunks
    final_df = pd.concat(results, ignore_index=True)
    return final_df

def create_large_csv_if_needed(file_path, num_rows=100000):
    """Create large CSV file if it doesn't exist"""
    if os.path.exists(file_path):
        print(f"✅ Large CSV file already exists: {file_path}")
        return
    
    print(f"Creating large CSV file with {num_rows:,} rows...")
    
    # Generate data
    data = {
        'id': range(1, num_rows + 1),
        'value': np.random.rand(num_rows) * 100,  # Random values 0-100
        'other': np.random.rand(num_rows) * 50,   # Random values 0-50
        'category': np.random.choice(['A', 'B', 'C', 'D'], num_rows),
        'score': np.random.randint(0, 100, num_rows)
    }
    
    # Create DataFrame and save
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)
    
    file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
    print(f"✅ Created: {file_path}")
    print(f"   Rows: {num_rows:,}")
    print(f"   File size: {file_size:.2f} MB")

def create_features_inefficient(data):
    """Creates features inefficiently - optimize"""
    features = []
    for value in data:
        feature_vector = np.array([
            value,
            value * 2,
            value ** 2,
            value + 10
        ], dtype=np.float64)
        features.append(feature_vector)
    return np.array(features)

def create_features_optimized(data):
    """Optimize for memory"""
    features = []
    for value in data:
        feature_vector = np.array([
            value,
            value * 2,
            value ** 2,
            value + 10
        ], dtype=np.float32)
        features.append(feature_vector)
    return np.array(features)


class DataProcessor:
    def __init__(self):
        self.cache = {}
        self.processed_data = []
    
    def process(self, data):
        """Process data and store in cache - find memory leak"""
        result = process_function(data)
        self.cache[data.id] = result  # Memory leak!
        self.processed_data.append(result)  # Another leak!
        return result

class DataProcessorOptimized:
    """
    Optimized data processor that avoids memory leaks.
    
    How it avoids leaks:
    1. Bounded cache (max_cache_size) - prevents unlimited growth
    2. LRU eviction - removes oldest entries automatically
    3. No processed_data storage - only cache what's needed
    4. Manual cleanup method - clear_cache() for explicit cleanup
    """
    def __init__(self, max_cache_size=100):
        """
        Initialize optimized processor.
        
        Args:
            max_cache_size: Maximum cache size (default: 100)
        """
        from collections import OrderedDict
        self.cache = OrderedDict()  # LRU cache
        self.max_cache_size = max_cache_size
        # ✅ Removed processed_data - not needed, was causing leak!
    
    def process(self, data):
        """
        Process data with bounded caching.
        
        Args:
            data: Data object with .id attribute
            
        Returns:
            Processed result
        """
        # Check cache first (O(1) lookup)
        if hasattr(data, 'id') and data.id in self.cache:
            # Move to end (mark as recently used - LRU)
            self.cache.move_to_end(data.id)
            return self.cache[data.id]
        
        # Process data (assuming process_function exists)
        # For demo, just return data * 2
        result = data * 2 if isinstance(data, (int, float)) else data
        
        # Add to cache
        if hasattr(data, 'id'):
            self.cache[data.id] = result
            
            # Remove oldest if cache too large (prevents memory leak!)
            if len(self.cache) > self.max_cache_size:
                self.cache.popitem(last=False)  # Remove oldest (FIFO)
        
        return result
    
    def clear_cache(self):
        """Clear cache to free memory"""
        self.cache.clear()
    
    def get_cache_size(self):
        """Get current cache size"""
        return len(self.cache)


    def feature_engineering_pipeline_inefficient(data_path):
        """Inefficient ML pipeline - optimize"""
        df = pd.read_csv(data_path)
        features = []
        for idx, row in df.iterrows():
            feature_dict = {
                'feature': row['value'] * 2,
                'feature2': row['value'] ** 2,
                'feature3': row['value'] + row['other'],
                'feature4': row['value'] * row['other'],
            }
            features.append(feature_dict)

        feature_df = pd.DataFrame(features)
        X = feature_df.values.astype(np.float64)
        return features
if __name__ == "__main__":
    #exercise_1_profile()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    current, peak = tracemalloc.get_traced_memory()
    result = create_features_optimized(np.random.rand(100000))
   
    print(f"Current: {current / 1024 / 1024:.2f} MB")
    print(f"Peak: {peak / 1024 / 1024:.2f} MB")

    tracemalloc.stop()

    print(result.shape)
    result_inefficient = create_features_inefficient(np.random.rand(100000))
    print(result_inefficient.shape)
    # large_file = os.path.join(script_dir, "large_file.csv")
    
    # # Create large CSV if it doesn't exist
    # create_large_csv_if_needed(large_file, num_rows=100000)
    
    # # Test chunked processing
    # print("\n" + "=" * 60)
    # print("Testing Chunked CSV Processing:")
    # print("=" * 60)
    
    # import tracemalloc
    # tracemalloc.start()
    
    # result = process_csv_chunked(large_file, chunk_size=10000)
    
    # current, peak = tracemalloc.get_traced_memory()
    # print(f"\nMemory Usage:")
    # print(f"  Current: {current / 1024 / 1024:.2f} MB")
    # print(f"  Peak: {peak / 1024 / 1024:.2f} MB")
    # print(f"\nResult shape: {result.shape}")
    # print(f"First few rows:")
    # print(result.head())
    
    # tracemalloc.stop()
    
    # # ✅ Fix: Get the script's directory to find files in same folder
  
    
    # print("=" * 60)
    # print("Testing load_file_generator:")
    # print("=" * 60)
    # print(f"Script directory: {script_dir}")
    # print(f"Current working directory: {os.getcwd()}")
    # print()
    
    # # # Option 1: Read a file in the same directory as the script
    # # exercises_file = os.path.join(script_dir, "01_memory_profiling_exercises.py")
    # # if os.path.exists(exercises_file):
    # #     print("Reading 01_memory_profiling_exercises.py:")
    # #     print("-" * 60)
    # #     for i, line in enumerate(load_file_generator(exercises_file), 1):
    # #         if i <= 10:  # Only show first 10 lines
    # #             print(f"{i:3}: {line}")
    # #         else:
    # #             print(f"... (showing first 10 lines only)")
    # #             break
    # # else:
    # #     print(f"File not found: {exercises_file}")
    
    # # # Option 2: Create a test file in script's directory
    # # print("\n" + "=" * 60)
    # # print("Creating and reading test file:")
    # # print("=" * 60)
    
    # # test_file = os.path.join(script_dir, "test_data.txt")
    # # with open(test_file, 'w') as f:
    # #     f.write("Line 1: Hello\n")
    # #     f.write("Line 2: World\n")
    # #     f.write("Line 3: Python\n")
    # #     f.write("Line 4: Generator\n")
    # #     f.write("Line 5: Memory Efficient!\n")
    
    # # print(f"Created test file: {test_file}")
    # # print("Reading with generator:")
    # # print("-" * 60)
    # # for line in load_file_generator(test_file):
    # #     print(f"Read: {line}")