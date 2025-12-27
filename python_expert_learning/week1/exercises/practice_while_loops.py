"""
Practice: While Loop Comparison Operators

Complete these exercises to master < vs <= and > vs >=
"""

# ============================================================================
# Exercise 1: Array Processing
# ============================================================================
# Process all elements in an array

def process_array(arr):
    """Process all elements in array"""
    i = 0
    # TODO: What operator should you use?
    while i ___ len(arr):  # Fill in: < or <=
        print(f"Element {i}: {arr[i]}")
        i += 1

# Test
# arr = [10, 20, 30, 40, 50]
# process_array(arr)
# Expected: Prints all 5 elements
# Hint: Array indices are 0 to len-1


# ============================================================================
# Exercise 2: Count Iterations
# ============================================================================
# Loop exactly 5 times

def loop_five_times():
    """Loop exactly 5 times"""
    i = 0
    count = 0
    # TODO: What operator should you use?
    while i ___ 5:  # Fill in: < or <=
        count += 1
        i += 1
    return count

# Test
# result = loop_five_times()
# assert result == 5, f"Expected 5, got {result}"
# Hint: We want 5 iterations (0, 1, 2, 3, 4)


# ============================================================================
# Exercise 3: Inclusive Range
# ============================================================================
# Print numbers from 1 to 10 (including 10)

def print_one_to_ten():
    """Print numbers 1 to 10 (inclusive)"""
    i = 1
    # TODO: What operator should you use?
    while i ___ 10:  # Fill in: < or <=
        print(i)
        i += 1

# Test
# print_one_to_ten()
# Expected: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
# Hint: We want to include 10


# ============================================================================
# Exercise 4: Two Pointers
# ============================================================================
# Reverse array using two pointers

def reverse_array(arr):
    """Reverse array in-place using two pointers"""
    left = 0
    right = len(arr) - 1
    
    # TODO: What operator should you use?
    while left ___ right:  # Fill in: < or <=
        # Swap
        arr[left], arr[right] = arr[right], arr[left]
        left += 1
        right -= 1
    
    return arr

# Test
# arr = [1, 2, 3, 4, 5]
# result = reverse_array(arr)
# assert result == [5, 4, 3, 2, 1]
# Hint: Stop when pointers meet (left == right)


# ============================================================================
# Exercise 5: Chunked Processing
# ============================================================================
# Process array in chunks

def process_chunks(arr, chunk_size=3):
    """Process array in chunks"""
    i = 0
    chunks = []
    
    # TODO: What operator should you use?
    while i ___ len(arr):  # Fill in: < or <=
        chunk = arr[i:i + chunk_size]
        chunks.append(chunk)
        i += chunk_size
    
    return chunks

# Test
# arr = list(range(10))
# chunks = process_chunks(arr, chunk_size=3)
# Expected: [[0,1,2], [3,4,5], [6,7,8], [9]]
# Hint: Process while there are elements left


# ============================================================================
# Exercise 6: Countdown
# ============================================================================
# Countdown from 10 to 1 (including 1)

def countdown():
    """Countdown from 10 to 1"""
    i = 10
    # TODO: What operator should you use?
    while i ___ 1:  # Fill in: >= or >
        print(i)
        i -= 1

# Test
# countdown()
# Expected: 10, 9, 8, 7, 6, 5, 4, 3, 2, 1
# Hint: We want to include 1


# ============================================================================
# Solutions
# ============================================================================

def solution_1():
    """Exercise 1: Array Processing"""
    arr = [10, 20, 30, 40, 50]
    i = 0
    while i < len(arr):  # ✅ < because indices are 0 to len-1
        print(f"Element {i}: {arr[i]}")
        i += 1

def solution_2():
    """Exercise 2: Count Iterations"""
    i = 0
    count = 0
    while i < 5:  # ✅ < because we want 5 iterations (0-4)
        count += 1
        i += 1
    return count

def solution_3():
    """Exercise 3: Inclusive Range"""
    i = 1
    while i <= 10:  # ✅ <= because we want to include 10
        print(i)
        i += 1

def solution_4():
    """Exercise 4: Two Pointers"""
    arr = [1, 2, 3, 4, 5]
    left = 0
    right = len(arr) - 1
    while left < right:  # ✅ < because we stop when they meet
        arr[left], arr[right] = arr[right], arr[left]
        left += 1
        right -= 1
    return arr

def solution_5():
    """Exercise 5: Chunked Processing"""
    arr = list(range(10))
    chunk_size = 3
    i = 0
    chunks = []
    while i < len(arr):  # ✅ < because we process while elements exist
        chunk = arr[i:i + chunk_size]
        chunks.append(chunk)
        i += chunk_size
    return chunks

def solution_6():
    """Exercise 6: Countdown"""
    i = 10
    while i >= 1:  # ✅ >= because we want to include 1
        print(i)
        i -= 1

if __name__ == "__main__":
    print("Complete the exercises above!")
    print("Think about:")
    print("1. Do I want to include the boundary?")
    print("2. Am I indexing an array?")
    print("3. How many iterations do I want?")










