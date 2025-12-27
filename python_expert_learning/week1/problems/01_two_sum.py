"""
Problem: Two Sum
Difficulty: Easy
LeetCode: https://leetcode.com/problems/two-sum/

Problem Statement:
Given an array of integers nums and an integer target, return indices of the two 
numbers such that they add up to target.

You may assume that each input would have exactly one solution, and you may not 
use the same element twice.

You can return the answer in any order.

Example 1:
Input: nums = [2,7,11,15], target = 9
Output: [0,1]
Explanation: Because nums[0] + nums[1] == 9, we return [0, 1].

Example 2:
Input: nums = [3,2,4], target = 6
Output: [1,2]

Example 3:
Input: nums = [3,3], target = 6
Output: [0,1]

Constraints:
- 2 <= nums.length <= 10^4
- -10^9 <= nums[i] <= 10^9
- -10^9 <= target <= 10^9
- Only one valid answer exists.
"""

# ============================================================================
# Solution 1: Brute Force (O(n²) time, O(1) space)
# ============================================================================

def two_sum_brute_force(nums, target):
    """
    Brute force approach: Check all pairs
    
    Time Complexity: O(n²) - nested loops
    Space Complexity: O(1) - no extra space
    """
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []


# ============================================================================
# Solution 2: Hash Map (O(n) time, O(n) space) - OPTIMAL
# ============================================================================

def two_sum_hash_map(nums, target):
    """
    Hash map approach: Store seen numbers and their indices
    
    Time Complexity: O(n) - single pass
    Space Complexity: O(n) - hash map storage
    
    Reasoning:
    - For each number, check if complement (target - num) exists in map
    - If yes, return indices
    - If no, store current number and index in map
    """
    seen = {}  # {number: index}
    
    for i, num in enumerate(nums):
        complement = target - num
        
        if complement in seen:
            return [seen[complement], i]
        
        seen[num] = i
    
    return []


# ============================================================================
# Solution 3: Two Pointers (O(n log n) time, O(1) space)
# ============================================================================
# Note: This requires sorting, so we need to track original indices

def two_sum_two_pointers(nums, target):
    """
    Two pointers approach: Sort and use two pointers
    Note: Need to track original indices
    
    Time Complexity: O(n log n) - sorting
    Space Complexity: O(n) - need to store original indices
    """
    # Create list of (value, original_index)
    indexed_nums = [(num, i) for i, num in enumerate(nums)]
    indexed_nums.sort()  # Sort by value
    
    left, right = 0, len(indexed_nums) - 1
    
    while left < right:
        current_sum = indexed_nums[left][0] + indexed_nums[right][0]
        
        if current_sum == target:
            return [indexed_nums[left][1], indexed_nums[right][1]]
        elif current_sum < target:
            left += 1
        else:
            right -= 1
    
    return []


# ============================================================================
# Optimal Solution (Recommended)
# ============================================================================

def two_sum(nums, target):
    """
    Optimal solution using hash map
    
    Time Complexity: O(n)
    Space Complexity: O(n)
    
    Reasoning:
    - Single pass through array
    - For each number, check if complement exists
    - Store seen numbers for O(1) lookup
    """
    seen = {}
    
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    
    return []


# ============================================================================
# Test Cases
# ============================================================================

def test_two_sum():
    """Test all solutions"""
    
    # Test case 1
    nums1 = [2, 7, 11, 15]
    target1 = 9
    result1 = two_sum(nums1, target1)
    assert result1 == [0, 1] or result1 == [1, 0], f"Test 1 failed: {result1}"
    print("✅ Test 1 passed")
    
    # Test case 2
    nums2 = [3, 2, 4]
    target2 = 6
    result2 = two_sum(nums2, target2)
    assert result2 == [1, 2] or result2 == [2, 1], f"Test 2 failed: {result2}"
    print("✅ Test 2 passed")
    
    # Test case 3
    nums3 = [3, 3]
    target3 = 6
    result3 = two_sum(nums3, target3)
    assert result3 == [0, 1] or result3 == [1, 0], f"Test 3 failed: {result3}"
    print("✅ Test 3 passed")
    
    # Edge case: Negative numbers
    nums4 = [-1, -2, -3, -4, -5]
    target4 = -8
    result4 = two_sum(nums4, target4)
    assert result4 == [2, 4] or result4 == [4, 2], f"Test 4 failed: {result4}"
    print("✅ Test 4 passed")
    
    print("\n🎉 All tests passed!")


# ============================================================================
# Performance Comparison
# ============================================================================

def compare_solutions():
    """Compare performance of different solutions"""
    import time
    
    # Large test case
    nums = list(range(10000))
    target = 19998  # Last two elements
    
    solutions = [
        ("Hash Map", two_sum_hash_map),
        ("Two Pointers", two_sum_two_pointers),
        ("Brute Force", two_sum_brute_force),
    ]
    
    print("\nPerformance Comparison:")
    print("-" * 50)
    
    for name, func in solutions:
        start = time.time()
        result = func(nums, target)
        end = time.time()
        print(f"{name:15} | Time: {(end - start) * 1000:.4f} ms | Result: {result}")
    
    print("\n💡 Hash Map is optimal for this problem!")


if __name__ == "__main__":
    test_two_sum()
    compare_solutions()
    
    print("\n" + "=" * 60)
    print("Key Takeaways:")
    print("=" * 60)
    print("1. Hash Map provides O(n) time complexity")
    print("2. Trade-off: O(n) space for O(n) time")
    print("3. Brute force is O(n²) but O(1) space")
    print("4. Choose based on constraints (time vs space)")

