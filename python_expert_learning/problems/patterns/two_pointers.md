# Two Pointers Pattern

## 🎯 When to Use
- Array is sorted
- Need to find pairs/triplets
- Palindrome checking
- Merging sorted arrays

## 📝 Template

```python
def two_pointers_template(arr):
    left = 0
    right = len(arr) - 1
    
    while left < right:
        # Process current pair
        if condition:
            # Move left pointer
            left += 1
        else:
            # Move right pointer
            right -= 1
    
    return result
```

## 🔍 Common Problems

### 1. Two Sum (Sorted Array)
```python
def two_sum_sorted(arr, target):
    left, right = 0, len(arr) - 1
    while left < right:
        current_sum = arr[left] + arr[right]
        if current_sum == target:
            return [left, right]
        elif current_sum < target:
            left += 1
        else:
            right -= 1
    return []
```

### 2. Valid Palindrome
```python
def is_palindrome(s):
    left, right = 0, len(s) - 1
    while left < right:
        if not s[left].isalnum():
            left += 1
        elif not s[right].isalnum():
            right -= 1
        elif s[left].lower() != s[right].lower():
            return False
        else:
            left += 1
            right -= 1
    return True
```

### 3. Container With Most Water
```python
def max_area(height):
    left, right = 0, len(height) - 1
    max_water = 0
    
    while left < right:
        width = right - left
        current_area = min(height[left], height[right]) * width
        max_water = max(max_water, current_area)
        
        if height[left] < height[right]:
            left += 1
        else:
            right -= 1
    
    return max_water
```

## ⏱️ Complexity
- **Time**: O(n)
- **Space**: O(1)

## ✅ Practice Problems
1. Two Sum (sorted)
2. 3Sum
3. Valid Palindrome
4. Container With Most Water
5. Trapping Rain Water

