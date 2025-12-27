"""
Problem 05: Longest Substring Without Repeating Characters

Given a string s, find the length of the longest substring without repeating characters.

Examples:
  s = "abcabcbb" -> 3  ("abc")
  s = "bbbbb" -> 1     ("b")
  s = "pwwkew" -> 3    ("wke")

Your task:
- Implement length_of_longest_substring(s).
- Add a few tests in __main__.
"""


def length_of_longest_substring(s: str) -> int:
    """
    Return the length of the longest substring without repeating characters.

    TODO: implement
    """
    raise NotImplementedError


if __name__ == "__main__":
    assert length_of_longest_substring("abcabcbb") == 3
    assert length_of_longest_substring("bbbbb") == 1
    assert length_of_longest_substring("pwwkew") == 3
    assert length_of_longest_substring("") == 0
    assert length_of_longest_substring(" ") == 1
    print("✅ Problem 05 tests passed")


