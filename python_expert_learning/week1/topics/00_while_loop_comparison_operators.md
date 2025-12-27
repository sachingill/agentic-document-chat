# While Loop: When to Use < vs <= or >= vs >

## 🎯 The Question

When writing while loops, how do you decide between:
- `<` vs `<=`
- `>` vs `>=`

---

## 📝 General Rule

### Use `<` or `>` when:
- **Exclusive boundary**: Don't include the boundary value
- **Count iterations**: Loop runs `n` times (0 to n-1)
- **Array/list indexing**: Access elements 0 to n-1

### Use `<=` or `>=` when:
- **Inclusive boundary**: Include the boundary value
- **Count to value**: Loop runs from start to end (inclusive)
- **Range operations**: Include both start and end

---

## 🔍 Examples

### Example 1: Counting Iterations

#### Using `<` (Exclusive - More Common)

```python
# Loop runs 5 times: 0, 1, 2, 3, 4
i = 0
while i < 5:
    print(i)
    i += 1
# Output: 0, 1, 2, 3, 4
```

**Why `<`?** We want exactly 5 iterations (0-4), not 6 (0-5).

#### Using `<=` (Inclusive)

```python
# Loop runs 6 times: 0, 1, 2, 3, 4, 5
i = 0
while i <= 5:
    print(i)
    i += 1
# Output: 0, 1, 2, 3, 4, 5
```

**Why `<=`?** We want to include 5 in the loop.

---

### Example 2: Array/List Indexing

#### Using `<` (Correct for Arrays)

```python
arr = [10, 20, 30, 40, 50]
i = 0
while i < len(arr):  # ✅ Correct: 0 to 4 (valid indices)
    print(arr[i])
    i += 1
# Output: 10, 20, 30, 40, 50
```

**Why `<`?** Array indices are 0 to len-1. Using `<=` would cause IndexError!

#### Using `<=` (Wrong - Causes Error!)

```python
arr = [10, 20, 30, 40, 50]
i = 0
while i <= len(arr):  # ❌ Wrong: tries to access index 5 (out of bounds!)
    print(arr[i])
    i += 1
# IndexError: list index out of range
```

---

### Example 3: Range Operations

#### Using `<=` (Inclusive Range)

```python
# Print numbers from 1 to 10 (inclusive)
i = 1
while i <= 10:
    print(i)
    i += 1
# Output: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
```

**Why `<=`?** We want to include 10.

#### Using `<` (Exclusive Range)

```python
# Print numbers from 1 to 9 (exclusive of 10)
i = 1
while i < 10:
    print(i)
    i += 1
# Output: 1, 2, 3, 4, 5, 6, 7, 8, 9
```

**Why `<`?** We don't want to include 10.

---

### Example 4: Processing in Chunks

#### Using `<` (Common Pattern)

```python
# Process array in chunks
arr = list(range(100))
chunk_size = 10
i = 0

while i < len(arr):  # ✅ Correct: process all elements
    chunk = arr[i:i + chunk_size]
    process(chunk)
    i += chunk_size
```

**Why `<`?** We process while there are elements left (i < len).

#### Using `<=` (Wrong - Skips Last Chunk!)

```python
arr = list(range(100))
chunk_size = 10
i = 0

while i <= len(arr):  # ❌ Wrong: might skip last chunk or cause error
    chunk = arr[i:i + chunk_size]
    process(chunk)
    i += chunk_size
```

---

### Example 5: Two Pointers Pattern

#### Using `<` (Common in Algorithms)

```python
# Two pointers: left and right
arr = [1, 2, 3, 4, 5]
left = 0
right = len(arr) - 1

while left < right:  # ✅ Correct: stop when they meet
    # Process
    left += 1
    right -= 1
```

**Why `<`?** We stop when pointers meet (left == right), not before.

#### Using `<=` (Processes Middle Element Twice!)

```python
arr = [1, 2, 3, 4, 5]
left = 0
right = len(arr) - 1

while left <= right:  # ⚠️ Processes middle element (if odd length)
    # Process
    left += 1
    right -= 1
```

**Why `<=`?** If you want to process the middle element when pointers meet.

---

## 🎯 Decision Tree

### Ask Yourself:

1. **Do I want to include the boundary value?**
   - Yes → Use `<=` or `>=`
   - No → Use `<` or `>`

2. **Am I indexing an array/list?**
   - Yes → Use `< len(arr)` (indices are 0 to len-1)
   - No → Depends on requirement

3. **How many iterations do I want?**
   - `n` iterations starting from 0 → Use `i < n`
   - `n` iterations including end → Use `i <= n-1` or `i < n`

4. **Am I using two pointers?**
   - Stop when they meet → Use `<`
   - Process when they meet → Use `<=`

---

## 📊 Common Patterns

### Pattern 1: Count Iterations

```python
# Loop n times (0 to n-1)
i = 0
while i < n:  # ✅ Most common
    # Do something
    i += 1
```

### Pattern 2: Process Array

```python
# Process all elements
i = 0
while i < len(arr):  # ✅ Always use < for arrays
    process(arr[i])
    i += 1
```

### Pattern 3: Range (Inclusive)

```python
# From start to end (inclusive)
i = start
while i <= end:  # ✅ Include end
    process(i)
    i += 1
```

### Pattern 4: Range (Exclusive)

```python
# From start to end (exclusive)
i = start
while i < end:  # ✅ Exclude end
    process(i)
    i += 1
```

### Pattern 5: Two Pointers

```python
# Stop when pointers meet
left = 0
right = len(arr) - 1
while left < right:  # ✅ Stop when they meet
    process(arr[left], arr[right])
    left += 1
    right -= 1
```

---

## ⚠️ Common Mistakes

### Mistake 1: Off-by-One Error with Arrays

```python
# ❌ WRONG
arr = [1, 2, 3, 4, 5]
i = 0
while i <= len(arr):  # Tries to access index 5 (out of bounds!)
    print(arr[i])
    i += 1

# ✅ CORRECT
arr = [1, 2, 3, 4, 5]
i = 0
while i < len(arr):  # Accesses indices 0-4 (valid)
    print(arr[i])
    i += 1
```

### Mistake 2: Missing Last Element

```python
# ❌ WRONG (if you want to include end)
i = 1
while i < 10:  # Stops at 9, missing 10
    print(i)
    i += 1

# ✅ CORRECT (if you want to include 10)
i = 1
while i <= 10:  # Includes 10
    print(i)
    i += 1
```

### Mistake 3: Infinite Loop

```python
# ❌ WRONG (infinite loop if condition never false)
i = 0
while i < 10:
    print(i)
    # Forgot i += 1!

# ✅ CORRECT
i = 0
while i < 10:
    print(i)
    i += 1  # Increment!
```

---

## 💡 Quick Reference

| Situation | Operator | Example |
|-----------|----------|---------|
| **Array indexing** | `<` | `while i < len(arr)` |
| **Count n times** | `<` | `while i < n` |
| **Range inclusive** | `<=` | `while i <= end` |
| **Range exclusive** | `<` | `while i < end` |
| **Two pointers** | `<` | `while left < right` |
| **Process middle** | `<=` | `while left <= right` |

---

## 🎯 Key Takeaways

1. **Arrays/Lists**: Always use `< len(arr)` (indices are 0 to len-1)
2. **Counting**: Use `< n` for n iterations (0 to n-1)
3. **Ranges**: Use `<=` if you want to include the end value
4. **Two Pointers**: Use `<` to stop when they meet, `<=` to process when they meet
5. **Think about boundaries**: Do you want to include the boundary value?

---

## ✅ Practice Questions

### Question 1: Process array elements
```python
arr = [1, 2, 3, 4, 5]
i = 0
while i ___ len(arr):  # What operator?
    print(arr[i])
    i += 1
```
**Answer**: `<` (indices are 0-4)

### Question 2: Print 1 to 10
```python
i = 1
while i ___ 10:  # What operator?
    print(i)
    i += 1
```
**Answer**: `<=` (want to include 10)

### Question 3: Loop 5 times
```python
i = 0
while i ___ 5:  # What operator?
    print(i)
    i += 1
```
**Answer**: `<` (want 5 iterations: 0, 1, 2, 3, 4)

---

**Remember: Think about what you want to include!** 🎯










