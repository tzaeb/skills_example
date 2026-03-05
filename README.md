# Skills Example

A minimal coding agent that uses **progressive skill disclosure** to keep context lean. Built to run against a [llama.cpp](https://github.com/ggerganov/llama.cpp) server via its OpenAI-compatible `/v1/chat/completions` endpoint.

Inspired by [Anthropic's Agent Skills architecture](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview).

## How it works

Skills are directories containing a `SKILL.md` file with YAML frontmatter. The agent loads them in three levels, only paying context cost for what's actually needed:

| Level | When loaded | What | Context cost |
|-------|------------|------|-------------|
| **1 - Metadata** | Always (startup) | `name` + `description` from YAML frontmatter | ~100 tokens/skill |
| **2 - Instructions** | On demand | Full body of `SKILL.md` | Only when triggered |
| **3 - Resources** | As needed | Extra files (e.g. `PATTERNS.md`, scripts) | Only when referenced |

After each completed question, loaded skill instructions are **pruned from context** so subsequent questions start clean. The LLM can always re-load a skill if needed.

```
Q1: "search for TODO in *.py"
  → load_skill("search-files")     # instructions loaded temporarily
  → python(search code)            # actual work
  → final answer
  → prune skill instructions       # context cleaned up

Q2: "read main.py"
  → clean context, no leftover from Q1
  → load_skill("read-file")        # fresh load
  → python(read code)
  → final answer
  → prune
```

## Project structure

```
skills_example/
├── main.py              # Interactive CLI
├── agent.py             # Agentic loop with progressive disclosure
├── tool_python.py       # Python interpreter (persistent namespace)
├── requirements.txt     # requests, pyyaml
└── skills/
    ├── __init__.py      # Skill loader (3-level progressive disclosure)
    ├── read-file/
    │   └── SKILL.md
    ├── write-file/
    │   └── SKILL.md
    ├── list-directory/
    │   └── SKILL.md
    ├── search-files/
    │   ├── SKILL.md
    │   └── PATTERNS.md  # Level 3 resource
    └── run-command/
        ├── SKILL.md
        └── STREAMING.md # Level 3 resource
```

## Quickstart

### Prerequisites

- Python 3.11+
- A running [llama.cpp server](https://github.com/ggerganov/llama.cpp/tree/master/examples/server) with a model that supports tool calling

### Install and run

```bash
pip install -r requirements.txt
python main.py --server http://localhost:8080 --workdir /path/to/project
```

### Example session

```
Agent ready. Server: http://localhost:8080
Working directory: /home/user/myproject
Skills loaded: read-file, write-file, list-directory, search-files, run-command

You> list the files here

  ⏳ thinking (step 1)...
────────────────────────────────────────────────────────────
📖 load_skill  list-directory
  Loaded 35 lines of instructions
────────────────────────────────────────────────────────────

  ⏳ thinking (step 2)...
────────────────────────────────────────────────────────────
▶ python  import os
  │ import os
  │ for entry in sorted(os.listdir(".")):
  │     suffix = "/" if os.path.isdir(entry) else ""
  │     print(f"  {entry}{suffix}")
  ┤ output:
  │   main.py
  │   src/
  │   tests/
────────────────────────────────────────────────────────────

  ⏳ thinking (step 3)...
  🧹 pruned 2 skill-context messages

Agent> Here are the files in your project: ...
```

## Tools exposed to the LLM

The agent provides three tools via llama.cpp's tool calling:

| Tool | Purpose |
|------|---------|
| `load_skill` | Load Level 2 instructions from a skill's `SKILL.md` |
| `read_resource` | Load Level 3 resources (extra docs, scripts) |
| `python` | Execute Python code to perform actions |

The LLM decides which skills to load based on the Level 1 metadata in the system prompt, then writes Python code following the loaded instructions.

## Creating a skill

Create a directory under `skills/` with a `SKILL.md` file:

```
skills/my-skill/
├── SKILL.md          # Required: frontmatter + instructions
├── REFERENCE.md      # Optional: extra documentation
└── scripts/
    └── helper.py     # Optional: utility scripts
```

The `SKILL.md` must have YAML frontmatter with `name` and `description`:

```markdown
---
name: my-skill
description: Brief description of what this does. Use when the user asks to ...
---

# My Skill

## Instructions

Step-by-step guidance with code examples for the LLM to follow.

For advanced usage, see [REFERENCE.md](REFERENCE.md).
```

The `description` field is what the LLM sees at all times (Level 1). Make it clear about **when** to use the skill.

## Security

The `python` tool runs LLM-generated code in a **subprocess** with full access to the filesystem, network, and shell. Each execution is isolated (no shared state between calls) and has a 30-second timeout, but it is **not sandboxed**. This means you should:

- **Only run this locally** on your own machine, not as a public-facing service
- **Review the code** the agent prints — every execution requires explicit approval (`y` to confirm)
- **Use `--workdir`** to scope file operations to a specific directory (note: this is not a sandbox, just a default `cwd`)

## Architecture

```
┌─────────────────────────────────────────────────────┐
│ System Prompt                                       │
│  ┌───────────────────────────────────────────────┐  │
│  │ Level 1: Skill metadata (always loaded)       │  │
│  │  - read-file: Read file contents...           │  │
│  │  - write-file: Write or create files...       │  │
│  │  - search-files: Search for patterns...       │  │
│  │  - ...                                        │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────┐
│ Agent Loop                                          │
│                                                     │
│  1. LLM sees metadata, picks relevant skill         │
│  2. load_skill("X") → Level 2 instructions loaded   │
│  3. read_resource("X", "Y.md") → Level 3 if needed  │
│  4. python(code) → executes action                  │
│  5. Loop until LLM gives final text response        │
│  6. Prune skill instructions from context           │
└─────────────────────────────────────────────────────┘
```
