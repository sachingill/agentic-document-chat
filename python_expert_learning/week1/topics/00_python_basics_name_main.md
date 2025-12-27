# Python Basics: `if __name__ == "__main__":` Explained

## 🎯 Why We Use `if __name__ == "__main__":`

This is a **Python best practice** that controls when code executes.

---

## 🔍 What is `__name__`?

`__name__` is a special Python variable that tells you:
- **If the file is run directly**: `__name__ == "__main__"`
- **If the file is imported**: `__name__ == "<filename>"`

---

## 📝 Example 1: Without `if __name__ == "__main__":`

### File: `my_module.py`
```python
def greet(name):
    print(f"Hello, {name}!")

# This runs ALWAYS - even when imported!
print("Module loaded!")
greet("World")
```

### File: `main.py` (imports my_module)
```python
import my_module

# Output:
# Module loaded!        ← Runs when imported!
# Hello, World!         ← Runs when imported!
```

**Problem**: Code runs even when you just want to import the module!

---

## ✅ Example 2: With `if __name__ == "__main__":`

### File: `my_module.py`
```python
def greet(name):
    print(f"Hello, {name}!")

# This only runs when file is executed directly
if __name__ == "__main__":
    print("Module loaded!")
    greet("World")
```

### File: `main.py` (imports my_module)
```python
import my_module

# Output: (nothing!)
# Code inside if __name__ == "__main__" doesn't run
```

### Running `my_module.py` directly:
```bash
python my_module.py
# Output:
# Module loaded!
# Hello, World!
```

**Solution**: Code only runs when you execute the file directly!

---

## 🎯 Real-World Use Cases

### Use Case 1: Testing Your Code

```python
def two_sum(nums, target):
    """Solution function"""
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []

# Test code - only runs when file is executed directly
if __name__ == "__main__":
    # Test cases
    assert two_sum([2, 7, 11, 15], 9) == [0, 1]
    assert two_sum([3, 2, 4], 6) == [1, 2]
    print("All tests passed!")
```

**Why**: 
- When you run the file: Tests execute
- When you import the function: Tests don't run (clean import)

---

### Use Case 2: Example/Demo Code

```python
def process_data(data):
    """Main function"""
    return data * 2

# Demo code - only runs when executed directly
if __name__ == "__main__":
    # Example usage
    result = process_data([1, 2, 3])
    print(f"Result: {result}")
```

**Why**:
- When you run the file: See the example
- When you import: Just get the function (no output)

---

### Use Case 3: Script vs Module

```python
# This file can be:
# 1. Imported as a module: import my_module
# 2. Run as a script: python my_module.py

def calculate_sum(a, b):
    return a + b

# Script behavior - only when run directly
if __name__ == "__main__":
    # Command-line script behavior
    import sys
    if len(sys.argv) == 3:
        a, b = int(sys.argv[1]), int(sys.argv[2])
        print(calculate_sum(a, b))
    else:
        print("Usage: python my_module.py <a> <b>")
```

**Why**:
- As module: Just import `calculate_sum`
- As script: Run from command line with arguments

---

## 🔍 How It Works

### When You Run a File Directly:
```python
# file.py
print(__name__)  # Output: __main__
```

### When You Import a File:
```python
# main.py
import file
# file.py's __name__ is "file" (not "__main__")
```

---

## ✅ Best Practices

### ✅ DO: Use `if __name__ == "__main__":` for:
- Test code
- Example/demo code
- Script entry points
- Performance profiling
- Debugging code

### ❌ DON'T: Put in `if __name__ == "__main__":`
- Function definitions (they should be importable)
- Class definitions (they should be importable)
- Constants (they should be importable)
- Import statements (usually)

---

## 📝 Common Pattern in Our Exercises

```python
def solution_function(input):
    """Main solution"""
    # Your code here
    pass

def test_solution():
    """Test the solution"""
    assert solution_function([1, 2, 3]) == expected
    print("Tests passed!")

# Only run tests when file is executed directly
if __name__ == "__main__":
    test_solution()
    # Or run examples
    result = solution_function([1, 2, 3])
    print(f"Result: {result}")
```

**Why This Pattern?**
1. **Reusable**: Others can import `solution_function`
2. **Testable**: Tests run when you execute the file
3. **Clean**: No side effects when imported
4. **Professional**: Standard Python practice

---

## 🎯 Key Takeaways

1. **`__name__ == "__main__"`** means "file is run directly"
2. **Use it** for code that should only run when executing the file
3. **Don't use it** for code that should be importable (functions, classes)
4. **Best practice** for making files both importable and executable

---

## 💡 Quick Reference

```python
# ✅ Good pattern
def my_function():
    pass

if __name__ == "__main__":
    # Test or demo code here
    my_function()

# ❌ Bad pattern
def my_function():
    pass

# Code runs even when imported!
my_function()
```

---

**This is why we use `if __name__ == "__main__":` in our exercises!** 🎯

