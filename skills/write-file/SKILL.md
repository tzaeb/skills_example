---
name: write-file
description: Write or create files with given content. Use when the user asks to create, write, edit, or modify files.
---

# Write File

## Instructions

Write content to a file, creating parent directories as needed.

```python
import os

path = "path/to/file.txt"
content = "file content here"

os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print(f"Written {len(content)} bytes to {path}")
```

For editing existing files, read first, modify, then write back:

```python
with open("path/to/file.txt", encoding="utf-8") as f:
    lines = f.readlines()

# Modify specific lines (0-indexed)
lines[5] = "replacement line\n"

with open("path/to/file.txt", "w", encoding="utf-8") as f:
    f.writelines(lines)
print("File updated")
```

## Guidelines

- Always create parent directories with `os.makedirs`
- Confirm the write by printing the path and bytes written
- When editing, read the file first to understand its structure
- Use UTF-8 encoding explicitly
