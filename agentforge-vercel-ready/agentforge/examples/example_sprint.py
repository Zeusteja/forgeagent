"""
Example: Use AgentForge programmatically to build a feature spec.

Run:
    ANTHROPIC_API_KEY=sk-... python examples/example_sprint.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agentforge.pipeline import Pipeline
from agentforge.models import AgentRole
from agentforge.utils import save_sprint


def main():
    title = "User Authentication System"
    description = """
    We need a secure user authentication system for our web app.
    Requirements:
    - Email + password registration and login
    - JWT-based session tokens (15 min access, 7 day refresh)
    - Rate limiting on login attempts (5 per minute)
    - Password reset via email
    - OAuth2 via Google (optional stretch)
    
    Tech stack: Python FastAPI backend, PostgreSQL, React frontend.
    """

    def on_done(agent, output):
        print(f"\n[{agent.emoji} {agent.name}]")
        for name, content in output.artifacts.items():
            print(f"  → {name}: {content[:200]}…" if len(content) > 200 else f"  → {name}: {content}")

    pipeline = Pipeline(verbose=True, on_agent_done=on_done)

    # Run only the planning + security agents (skip straight to code review)
    outputs = pipeline.run(
        title=title,
        description=description,
        pipeline=[AgentRole.CEO, AgentRole.ARCHITECT, AgentRole.SECURITY, AgentRole.DOCS],
    )

    path = save_sprint(outputs, title)
    print(f"\n✅  Report: {path}")


if __name__ == "__main__":
    main()
