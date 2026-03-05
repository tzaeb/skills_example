"""
Python interpreter for the agent.

Executes code in a subprocess, capturing stdout/stderr.
This is the agent's primary way to interact with the filesystem and
perform actions described by skills.
"""

import os
import subprocess
import sys
import tempfile


class PythonInterpreter:
    def __init__(self, working_dir: str = "."):
        self.working_dir = os.path.abspath(working_dir)

    def execute(self, code: str, timeout: int = 30) -> str:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(code)
            tmp_path = f.name

        try:
            result = subprocess.run(
                [sys.executable, tmp_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.working_dir,
            )
        except subprocess.TimeoutExpired:
            return f"[ERROR]\nExecution timed out after {timeout}s"
        finally:
            os.unlink(tmp_path)

        stdout = result.stdout
        stderr = result.stderr

        output = ""
        if stdout:
            output += stdout
        if stderr:
            output += f"\n[ERROR]\n{stderr}"

        return output.strip() if output.strip() else "(no output)"
