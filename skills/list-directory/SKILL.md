---
name: list-directory
description: List files and directories at a given path. Use when the user asks to see what files exist, explore a project structure, or navigate directories.
---

# List Directory

## Instructions

List directory contents using `os.listdir` or `os.walk` for recursive listing.

```python
import os

path = "."
for entry in sorted(os.listdir(path)):
    full = os.path.join(path, entry)
    indicator = "/" if os.path.isdir(full) else ""
    print(f"  {entry}{indicator}")
```

For recursive/tree listing:

```python
import os

def show_tree(path, prefix="", max_depth=3, depth=0):
    if depth >= max_depth:
        return
    entries = sorted(os.listdir(path))
    dirs = [e for e in entries if os.path.isdir(os.path.join(path, e)) and not e.startswith(".")]
    files = [e for e in entries if not os.path.isdir(os.path.join(path, e))]
    for f in files:
        print(f"{prefix}{f}")
    for d in dirs:
        print(f"{prefix}{d}/")
        show_tree(os.path.join(path, d), prefix + "  ", max_depth, depth + 1)

show_tree(".")
```

## Guidelines

- Skip hidden files/dirs (starting with `.`) in tree views unless explicitly asked
- Show directories with a trailing `/` indicator
- For deep trees, default to max depth of 3 to avoid noise
