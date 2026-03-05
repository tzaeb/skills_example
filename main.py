#!/usr/bin/env python3
"""
Interactive agent CLI powered by llama.cpp server.

Usage:
    python main.py [--server URL] [--workdir PATH]

Requires a running llama.cpp server with a model that supports tool calling.
"""

import argparse
import sys

from agent import Agent, Color


def main():
    parser = argparse.ArgumentParser(description="Agent with skills via llama.cpp")
    parser.add_argument(
        "--server", default="http://localhost:8080",
        help="llama.cpp server URL (default: http://localhost:8080)",
    )
    parser.add_argument(
        "--workdir", default=".",
        help="Working directory for file operations (default: current dir)",
    )
    args = parser.parse_args()

    agent = Agent(server_url=args.server, working_dir=args.workdir)

    print(f"Agent ready. Server: {args.server}")
    print(f"Working directory: {args.workdir}")
    print(f"Skills loaded: {', '.join(agent.skills.keys())}")
    print("Type your message (Ctrl+C to exit):\n")

    while True:
        try:
            user_input = input(f"{Color.BOLD}{Color.BLUE}You>{Color.RESET} ").strip()
            if not user_input:
                continue

            response = agent.run(user_input)
            print(f"\n{Color.BOLD}{Color.GREEN}Agent>{Color.RESET} {response}\n")

        except KeyboardInterrupt:
            print("\nBye!")
            sys.exit(0)
        except Exception as e:
            print(f"\nError: {e}")


if __name__ == "__main__":
    main()
