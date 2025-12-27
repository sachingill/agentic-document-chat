"""
Problem 02: Valid Anagram

Given two strings s and t, return True if t is an anagram of s, and False otherwise.

Notes:
- An anagram uses the same characters with the same counts, but possibly different order.

Examples:
  s = "anagram", t = "nagaram" -> True
  s = "rat", t = "car" -> False

Constraints (typical interview):
- 1 <= len(s), len(t) <= 10^5
- s and t consist of lowercase English letters

Your task:
- Implement is_anagram(s, t) with good time/space complexity.
- Add a few tests in __main__.
"""


def is_anagram(s: str, t: str) -> bool:
    """
    Return True if t is an anagram of s.

    TODO: implement
    """
    
    raise NotImplementedError


if __name__ == "__main__":
    # Minimal tests (add more)
    assert is_anagram("anagram", "nagaram") is True
    assert is_anagram("rat", "car") is False
    assert is_anagram("", "") is True
    assert is_anagram("a", "a") is True
    assert is_anagram("ab", "a") is False
    print("✅ Problem 02 tests passed")


