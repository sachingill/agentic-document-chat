"""
Blind 75 (tracker-driven) file generator.

Creates one separate stub `.py` file per unchecked item in TRACKER.md.
No solutions are generated — only prompts + function stub + test placeholders.

Run (from repo root):
  python python_expert_learning/problems/blind75/generate_files.py

Output:
  python_expert_learning/problems/blind75/problems/
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


HERE = Path(__file__).resolve().parent
TRACKER = HERE / "TRACKER.md"
OUT_DIR = HERE / "problems"


@dataclass(frozen=True)
class ProblemItem:
    category: str
    name: str


def slugify(text: str) -> str:
    s = text.strip().lower()
    s = s.replace("&", "and")
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "problem"


def parse_tracker(md: str) -> list[ProblemItem]:
    items: list[ProblemItem] = []
    category = "Uncategorized"
    for raw in md.splitlines():
        line = raw.strip()
        if line.startswith("## "):
            category = line[3:].strip()
            continue
        m = re.match(r"^- \[\s\]\s+(.*)$", line)
        if m:
            name = m.group(1).strip()
            items.append(ProblemItem(category=category, name=name))
    return items


def function_name_from_problem(name: str) -> str:
    # Simple heuristic: create a stable snake_case name
    base = slugify(name)
    # avoid leading digits
    if base and base[0].isdigit():
        base = f"p_{base}"
    return base


def render_file(*, idx: int, item: ProblemItem) -> str:
    func = function_name_from_problem(item.name)
    return f'''"""
Blind 75
Category: {item.category}
Problem {idx:03d}: {item.name}

Task:
- Implement `{func}(...)`
- Add/extend tests under __main__

Notes:
- No solutions are provided here. Implement yourself, then run the tests.
"""


def {func}(*args, **kwargs):
    """TODO: implement"""
    raise NotImplementedError


if __name__ == "__main__":
    # Sample test harness (add real cases for: {item.name})
    #
    # Use this shape:
    # tests = [
    #   ((arg1, arg2), {{"kw": 1}}, expected),
    # ]
    tests = []

    for i, (args, kwargs, expected) in enumerate(tests, start=1):
        got = {func}(*args, **kwargs)
        assert got == expected, f"case {{i}} failed: got={{got!r}} expected={{expected!r}}"

    print("✅ Add tests to 'tests' list, then implement the function.")
'''


def main() -> None:
    if not TRACKER.exists():
        raise SystemExit(f"Missing tracker: {TRACKER}")

    md = TRACKER.read_text(encoding="utf-8")
    items = parse_tracker(md)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    created = 0
    skipped = 0
    for i, item in enumerate(items, start=1):
        fname = f"{i:03d}_{slugify(item.name)}.py"
        out = OUT_DIR / fname
        if out.exists():
            skipped += 1
            continue
        out.write_text(render_file(idx=i, item=item), encoding="utf-8")
        created += 1

    print(f"Generated stubs in: {OUT_DIR}")
    print(f"Total items in tracker: {len(items)}")
    print(f"Created new files: {created}")
    print(f"Skipped existing files: {skipped}")


if __name__ == "__main__":
    main()


