---
name: search-files
description: Search for text patterns across files using regex. Use when the user asks to find, grep, or search for code, text, or patterns in files.
---

# Search Files

## Instructions

Search for a pattern across files using `re` and `os.walk`.

```python
import os, re

pattern = re.compile(r"your_pattern_here")
search_path = "."

for root, dirs, files in os.walk(search_path):
    # Skip hidden and common non-source directories
    dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "__pycache__", ".git")]
    for fname in files:
        fpath = os.path.join(root, fname)
        try:
            with open(fpath, encoding="utf-8", errors="ignore") as f:
                for i, line in enumerate(f, 1):
                    if pattern.search(line):
                        print(f"{fpath}:{i}: {line.rstrip()}")
        except (PermissionError, OSError):
            continue
```

To filter by file extension:

```python
import fnmatch
# Inside the loop, add:
if not fnmatch.fnmatch(fname, "*.py"):
    continue
```

## Guidelines

- Skip `.git`, `node_modules`, `__pycache__`, and other non-source directories
- Use `errors="ignore"` to handle binary files
- Show results as `filepath:line_number: matching_line`
- Use `re.IGNORECASE` for case-insensitive search when appropriate

For advanced search patterns, see [PATTERNS.md](PATTERNS.md).
