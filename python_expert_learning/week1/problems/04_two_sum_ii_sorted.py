"""
Problem 04: Two Sum II (Input Array Is Sorted)

Given a 1-indexed array of integers numbers that is already sorted in non-decreasing order,
find two numbers such that they add up to a specific target number.

Return the indices of the two numbers (1-indexed) as a list: [index1, index2],
where 1 <= index1 < index2 <= len(numbers).

Assume there is exactly one solution. You may not use the same element twice.

Example:
  numbers = [2,7,11,15], target = 9 -> [1,2]

Your task:
- Implement two_sum_sorted(numbers, target) using O(1) extra space.
- Add a few tests in __main__.
"""

from typing import List


def two_sum_sorted(numbers: List[int], target: int) -> List[int]:
    """
    Return 1-based indices of two numbers summing to target.

    TODO: implement
    """
    raise NotImplementedError


if __name__ == "__main__":
    assert two_sum_sorted([2, 7, 11, 15], 9) == [1, 2]
    assert two_sum_sorted([2, 3, 4], 6) == [1, 3]
    assert two_sum_sorted([-1, 0], -1) == [1, 2]
    print("✅ Problem 04 tests passed")


