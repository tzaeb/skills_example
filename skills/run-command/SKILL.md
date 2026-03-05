---
name: run-command
description: Run shell commands (git, build tools, tests, package managers, etc). Use when the user asks to run, execute, build, test, or install something.
---

# Run Command

## Instructions

Execute shell commands using `subprocess` and capture output.

```python
import subprocess

result = subprocess.run(
    ["git", "status"],
    capture_output=True, text=True, timeout=30
)
print(result.stdout)
if result.returncode != 0:
    print(f"STDERR: {result.stderr}")
    print(f"Exit code: {result.returncode}")
```

For commands that need shell features (pipes, redirection):

```python
import subprocess

result = subprocess.run(
    "ls -la | head -20",
    shell=True, capture_output=True, text=True, timeout=30
)
print(result.stdout)
```

For long-running commands, use a longer timeout or stream output. See [STREAMING.md](STREAMING.md).

## Guidelines

- Always set a `timeout` to prevent hanging
- Prefer list form (`["cmd", "arg"]`) over `shell=True` when possible
- Always check `returncode` and show stderr on failure
- Print the output so the user can see the results
