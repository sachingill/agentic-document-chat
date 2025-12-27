"""
Blind 75
Category: Linked List
Problem 034: Reverse Linked List

Task:
- Implement `reverse_linked_list(...)`
- Add/extend tests under __main__

Notes:
- No solutions are provided here. Implement yourself, then run the tests.
"""


def reverse_linked_list(*args, **kwargs):
    """TODO: implement"""
    raise NotImplementedError

if __name__ == "__main__":
    # Sample test harness (add real cases based on the prompt)
    #
    # Use this shape:
    # tests = [
    #   ((arg1, arg2), {"kw": 1}, expected),
    # ]
    tests = []

    for i, (args, kwargs, expected) in enumerate(tests, start=1):
        got = reverse_linked_list(*args, **kwargs)
        assert got == expected, f"case {i} failed: got={got!r} expected={expected!r}"

    print("✅ Add tests to 'tests' list, then implement reverse_linked_list().")

