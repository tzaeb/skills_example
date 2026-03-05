"""
Agentic loop using llama.cpp server's /v1/chat/completions endpoint.

Implements progressive skill disclosure:
- Level 1: Skill metadata is always in the system prompt
- Level 2: Skill instructions are loaded on-demand via the `load_skill` tool
- Level 3: Resources (extra docs, scripts) are loaded as-needed via `read_resource`

The agent also has a `python` tool for executing code to perform actions.
"""

import json
import textwrap
from pathlib import Path

import requests


# ANSI color codes for terminal output
class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CYAN = "\033[36m"
    YELLOW = "\033[33m"
    GREEN = "\033[32m"
    MAGENTA = "\033[35m"
    BLUE = "\033[34m"
    RED = "\033[31m"

from skills import (
    discover_all_skills,
    build_metadata_prompt,
    load_skill_instructions,
    load_skill_resource,
    SKILLS_DIR,
)
from tool_python import PythonInterpreter

TOOL_PYTHON = {
    "type": "function",
    "function": {
        "name": "python",
        "description": (
            "Execute Python code to perform tasks. You have the full Python "
            "standard library and filesystem access. Use print() to return "
            "results. The namespace persists across calls."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute",
                }
            },
            "required": ["code"],
        },
    },
}

TOOL_LOAD_SKILL = {
    "type": "function",
    "function": {
        "name": "load_skill",
        "description": (
            "Load the full instructions for a skill. Call this before performing "
            "a task to get detailed guidance and code examples. Pass the skill name."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the skill to load (e.g. 'read-file', 'run-command')",
                }
            },
            "required": ["name"],
        },
    },
}

TOOL_READ_RESOURCE = {
    "type": "function",
    "function": {
        "name": "read_resource",
        "description": (
            "Read an additional resource file from a skill directory. Use this "
            "when skill instructions reference extra documentation like PATTERNS.md "
            "or STREAMING.md."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "skill_name": {
                    "type": "string",
                    "description": "Name of the skill that owns the resource",
                },
                "resource": {
                    "type": "string",
                    "description": "Filename of the resource (e.g. 'PATTERNS.md')",
                },
            },
            "required": ["skill_name", "resource"],
        },
    },
}

SYSTEM_PROMPT = """\
You are a helpful coding agent. You perform tasks by writing and executing Python code.

## How to work

1. When a task matches a skill, first call `load_skill` to get detailed instructions.
2. Follow the loaded instructions and use the `python` tool to execute code.
3. If instructions reference additional resources (like PATTERNS.md), use `read_resource` to load them.
4. Always use print() in your Python code so the user can see results.

## {skills_metadata}
"""


class Agent:
    def __init__(self, server_url: str = "http://localhost:8080", working_dir: str = "."):
        self.server_url = server_url.rstrip("/")
        self.interpreter = PythonInterpreter(working_dir)
        self.tools = [TOOL_PYTHON, TOOL_LOAD_SKILL, TOOL_READ_RESOURCE]
        self.messages = []

        self._step_count = 0

        # Level 1: discover skills and put metadata in system prompt
        self.skills = discover_all_skills()
        metadata_prompt = build_metadata_prompt(self.skills)
        self.system_message = {
            "role": "system",
            "content": SYSTEM_PROMPT.format(skills_metadata=metadata_prompt),
        }

    def _find_skill_dir(self, name: str) -> Path | None:
        """Resolve a skill name to its directory path."""
        if name in self.skills:
            return Path(self.skills[name]["path"])
        # Fallback: try finding by directory name
        candidate = (SKILLS_DIR / name).resolve()
        if not str(candidate).startswith(str(SKILLS_DIR.resolve())):
            return None
        if candidate.is_dir():
            return candidate
        return None

    def chat_completion(self, messages: list[dict]) -> dict:
        payload = {
            "messages": [self.system_message] + messages,
            "tools": self.tools,
            "tool_choice": "auto",
        }

        resp = requests.post(
            f"{self.server_url}/v1/chat/completions",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        return resp.json()

    def _print_tool_header(self, icon: str, label: str, detail: str):
        print(f"\n{Color.DIM}{'─' * 60}{Color.RESET}")
        print(f"{Color.BOLD}{icon} {label}{Color.RESET} {Color.DIM}{detail}{Color.RESET}")

    def _print_tool_output(self, output: str, max_lines: int = 15):
        lines = output.splitlines()
        preview = lines[:max_lines]
        for line in preview:
            print(f"  {Color.DIM}│{Color.RESET} {line}")
        if len(lines) > max_lines:
            print(f"  {Color.DIM}│ ... ({len(lines) - max_lines} more lines){Color.RESET}")
        print(f"{Color.DIM}{'─' * 60}{Color.RESET}")

    def handle_tool_call(self, tc: dict) -> str:
        func_name = tc["function"]["name"]
        args = json.loads(tc["function"]["arguments"])

        if func_name == "python":
            code = args["code"]
            self._print_tool_header("▶", "python", "")
            # Show the full code indented
            for line in code.strip().splitlines():
                print(f"  {Color.CYAN}│{Color.RESET} {Color.DIM}{line}{Color.RESET}")
            confirm = input(f"  {Color.YELLOW}Execute? [y/N]{Color.RESET} ").strip().lower()
            if confirm != "y":
                return "(execution skipped by user)"
            output = self.interpreter.execute(code)
            print(f"  {Color.GREEN}┤ output:{Color.RESET}")
            self._print_tool_output(output)
            return output

        elif func_name == "load_skill":
            # Level 2: load full instructions
            self._print_tool_header("📖", "load_skill", args["name"])
            skill_dir = self._find_skill_dir(args["name"])
            if not skill_dir:
                print(f"  {Color.RED}Skill not found{Color.RESET}")
                return f"Skill '{args['name']}' not found."
            instructions = load_skill_instructions(skill_dir)
            line_count = len(instructions.splitlines()) if instructions else 0
            print(f"  {Color.GREEN}Loaded {line_count} lines of instructions{Color.RESET}")
            print(f"{Color.DIM}{'─' * 60}{Color.RESET}")
            return instructions or f"No instructions found for '{args['name']}'."

        elif func_name == "read_resource":
            # Level 3: load additional resource
            detail = f"{args['skill_name']}/{args['resource']}"
            self._print_tool_header("📎", "read_resource", detail)
            skill_dir = self._find_skill_dir(args["skill_name"])
            if not skill_dir:
                print(f"  {Color.RED}Skill not found{Color.RESET}")
                return f"Skill '{args['skill_name']}' not found."
            content = load_skill_resource(skill_dir, args["resource"])
            line_count = len(content.splitlines()) if content else 0
            print(f"  {Color.GREEN}Loaded {line_count} lines{Color.RESET}")
            print(f"{Color.DIM}{'─' * 60}{Color.RESET}")
            return content or f"Resource '{args['resource']}' not found."

        return f"Unknown tool: {func_name}"

    def handle_tool_calls(self, tool_calls: list[dict]) -> list[dict]:
        results = []
        for tc in tool_calls:
            output = self.handle_tool_call(tc)
            results.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": output,
            })
        return results

    def step(self, user_message: str | None = None) -> str | None:
        """Run one step. Returns assistant text if done, None if more tool calls needed."""
        if user_message:
            self.messages.append({"role": "user", "content": user_message})

        self._step_count += 1
        print(f"{Color.DIM}  ⏳ thinking (step {self._step_count})...{Color.RESET}", flush=True)

        response = self.chat_completion(self.messages)
        choice = response["choices"][0]
        assistant_msg = choice["message"]
        self.messages.append(assistant_msg)

        # Print any inline text the LLM included alongside tool calls
        if assistant_msg.get("content") and assistant_msg.get("tool_calls"):
            print(f"\n{Color.MAGENTA}  💭 {assistant_msg['content']}{Color.RESET}")

        if assistant_msg.get("tool_calls"):
            tool_results = self.handle_tool_calls(assistant_msg["tool_calls"])
            self.messages.extend(tool_results)
            return None

        return assistant_msg.get("content", "")

    def _prune_skill_context(self):
        """Remove skill/resource tool calls and their responses from history.

        After the agent finishes answering a question, the loaded SKILL.md
        instructions and resources are no longer needed. Pruning them keeps
        the context lean for subsequent questions - the LLM can always
        re-load a skill via load_skill if needed again.

        We keep:
        - user messages
        - assistant messages (final text responses)
        - python tool calls + results (they represent actual work done)

        We remove:
        - assistant messages that ONLY contained load_skill/read_resource calls
        - the corresponding tool response messages
        """
        SKILL_TOOLS = {"load_skill", "read_resource"}

        # Collect tool_call_ids that belong to skill-loading calls
        skill_call_ids = set()
        for msg in self.messages:
            if msg.get("role") == "assistant" and msg.get("tool_calls"):
                for tc in msg["tool_calls"]:
                    if tc["function"]["name"] in SKILL_TOOLS:
                        skill_call_ids.add(tc["id"])

        pruned = []
        for msg in self.messages:
            # Drop tool responses for skill-loading calls
            if msg.get("role") == "tool" and msg.get("tool_call_id") in skill_call_ids:
                continue

            # For assistant messages with tool_calls, strip out skill-loading calls
            if msg.get("role") == "assistant" and msg.get("tool_calls"):
                remaining_calls = [
                    tc for tc in msg["tool_calls"]
                    if tc["function"]["name"] not in SKILL_TOOLS
                ]
                if remaining_calls:
                    # Keep the message but with only non-skill tool calls
                    pruned_msg = dict(msg)
                    pruned_msg["tool_calls"] = remaining_calls
                    pruned.append(pruned_msg)
                elif msg.get("content"):
                    # Had text alongside skill calls - keep just the text
                    pruned.append({"role": "assistant", "content": msg["content"]})
                # else: message was purely skill-loading calls, drop entirely
                continue

            pruned.append(msg)

        removed = len(self.messages) - len(pruned)
        if removed > 0:
            print(f"{Color.DIM}  🧹 pruned {removed} skill-context messages{Color.RESET}")
        self.messages = pruned

    def run(self, user_message: str, max_steps: int = 20) -> str:
        """Run the full agent loop until the LLM responds with text (no tool calls)."""
        self._step_count = 0
        result = self.step(user_message)

        steps = 0
        while result is None and steps < max_steps:
            result = self.step()
            steps += 1

        if result is None:
            return "(Agent reached maximum steps without a final response)"

        # Prune loaded skill instructions from history - they served their
        # purpose for this question. The LLM can re-load them if needed
        # for the next question (Level 1 metadata stays in system prompt).
        self._prune_skill_context()

        return result
