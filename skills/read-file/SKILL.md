---
name: read-file
description: Read the contents of a file at a given path. Use when the user asks to view, inspect, or read a file.
---

# Read File

## Instructions

Read file contents using Python's built-in `open()`. Always use UTF-8 encoding with error handling for binary files.

```python
with open("path/to/file.txt", encoding="utf-8", errors="replace") as f:
    content = f.read()
print(content)
```

For large files, read only what's needed:

```python
with open("path/to/file.txt", encoding="utf-8", errors="replace") as f:
    for i, line in enumerate(f, 1):
        print(f"{i:4d} | {line}", end="")
        if i >= 100:
            print(f"\n... (truncated, file has more lines)")
            break
```

## Guidelines

- Always print the content so the user can see it
- Use `errors="replace"` to handle binary/non-UTF8 files gracefully
- For very large files, show the first ~100 lines and note the truncation
- Show line numbers when displaying code files
