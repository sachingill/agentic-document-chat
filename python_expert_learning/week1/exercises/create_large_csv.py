"""
Script to create a large CSV file for testing chunked processing
"""

import pandas as pd
import numpy as np
import os

def create_large_csv(file_path, num_rows=100000):
    """
    Create a large CSV file for testing.
    
    Args:
        file_path: Path where CSV will be saved
        num_rows: Number of rows to generate (default: 100,000)
    """
    print(f"Creating large CSV file with {num_rows:,} rows...")
    
    # Generate data
    data = {
        'id': range(1, num_rows + 1),
        'value': np.random.rand(num_rows) * 100,  # Random values 0-100
        'other': np.random.rand(num_rows) * 50,   # Random values 0-50
        'category': np.random.choice(['A', 'B', 'C', 'D'], num_rows),
        'score': np.random.randint(0, 100, num_rows)
    }
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Save to CSV
    df.to_csv(file_path, index=False)
    
    # Get file size
    file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
    
    print(f"✅ Created: {file_path}")
    print(f"   Rows: {num_rows:,}")
    print(f"   Columns: {len(df.columns)}")
    print(f"   File size: {file_size:.2f} MB")
    print(f"   Memory usage (if loaded): ~{df.memory_usage(deep=True).sum() / (1024 * 1024):.2f} MB")
    
    return df

if __name__ == "__main__":
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    large_file = os.path.join(script_dir, "large_file.csv")
    
    # Create large CSV (100,000 rows)
    # Adjust num_rows for larger/smaller files:
    # - 10,000 rows: ~1 MB
    # - 100,000 rows: ~10 MB
    # - 1,000,000 rows: ~100 MB
    create_large_csv(large_file, num_rows=100000)
    
    print("\n" + "=" * 60)
    print("File created! You can now test chunked processing.")
    print("=" * 60)

