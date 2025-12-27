"""
One-time updater: add a test harness block to existing generated stub files.

This does NOT add solutions. It only replaces the existing __main__ block with a
standard harness where you can paste sample test cases.

Run:
  python python_expert_learning/problems/blind75/add_test_harness_to_stubs.py
"""

from __future__ import annotations

import re
from pathlib import Path


HERE = Path(__file__).resolve().parent
PROBLEMS_DIR = HERE / "problems"


MAIN_BLOCK = """if __name__ == "__main__":
    # Sample test harness (add real cases based on the prompt)
    #
    # Use this shape:
    # tests = [
    #   ((arg1, arg2), {"kw": 1}, expected),
    # ]
    tests = []

    for i, (args, kwargs, expected) in enumerate(tests, start=1):
        got = solve(*args, **kwargs)
        assert got == expected, f"case {i} failed: got={got!r} expected={expected!r}"

    print("✅ Add tests to 'tests' list, then implement solve().")
"""


def extract_function_name(src: str) -> str:
    # first "def <name>(" that isn't inside triple quotes is hard to parse perfectly;
    # use simple heuristic: pick the first def at column 0.
    m = re.search(r"^def\s+([a-zA-Z_]\w*)\s*\(", src, flags=re.MULTILINE)
    return m.group(1) if m else "solve"


def replace_main_block(src: str, func_name: str) -> str:
    new_main = MAIN_BLOCK.replace("solve", func_name)
    if 'if __name__ == "__main__":' not in src:
        return src.rstrip() + "\n\n" + new_main + "\n"

    # Replace everything from the if __main__ line to the end of file.
    prefix = src.split('if __name__ == "__main__":', 1)[0].rstrip() + "\n\n"
    return prefix + new_main + "\n"


def main() -> None:
    if not PROBLEMS_DIR.exists():
        raise SystemExit(f"Missing directory: {PROBLEMS_DIR}")

    updated = 0
    for path in sorted(PROBLEMS_DIR.glob("*.py")):
        src = path.read_text(encoding="utf-8")
        fn = extract_function_name(src)
        out = replace_main_block(src, fn)
        if out != src:
            path.write_text(out, encoding="utf-8")
            updated += 1

    print(f"Updated __main__ harness in {updated} files under {PROBLEMS_DIR}")


if __name__ == "__main__":
    main()


