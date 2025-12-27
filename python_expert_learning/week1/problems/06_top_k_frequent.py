"""
Problem 06: Top K Frequent Elements

Given an integer array nums and an integer k, return the k most frequent elements.
You may return the answer in any order.

Examples:
  nums = [1,1,1,2,2,3], k = 2 -> [1,2]
  nums = [1], k = 1 -> [1]

Your task:
- Implement top_k_frequent(nums, k).
- Add a few tests in __main__.
"""

from typing import List


def top_k_frequent(nums: List[int], k: int) -> List[int]:
    """
    Return the k most frequent elements.

    TODO: implement
    """
    raise NotImplementedError


if __name__ == "__main__":
    out = top_k_frequent([1, 1, 1, 2, 2, 3], 2)
    assert set(out) == {1, 2}
    assert top_k_frequent([1], 1) == [1]
    print("✅ Problem 06 tests passed")


