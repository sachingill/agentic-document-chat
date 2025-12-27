"""
Problem 03: Contains Duplicate

Given an integer array nums, return True if any value appears at least twice in the array,
and return False if every element is distinct.

Examples:
  nums = [1,2,3,1] -> True
  nums = [1,2,3,4] -> False
  nums = [] -> False

Your task:
- Implement contains_duplicate(nums).
- Add a few tests in __main__.
"""

from typing import List


def contains_duplicate(nums: List[int]) -> bool:
    """
    Return True if nums contains any duplicate.

    TODO: implement
    """
    raise NotImplementedError


if __name__ == "__main__":
    assert contains_duplicate([1, 2, 3, 1]) is True
    assert contains_duplicate([1, 2, 3, 4]) is False
    assert contains_duplicate([]) is False
    assert contains_duplicate([0]) is False
    assert contains_duplicate([0, 0]) is True
    print("✅ Problem 03 tests passed")


