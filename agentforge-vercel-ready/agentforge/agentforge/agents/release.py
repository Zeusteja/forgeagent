"""Release Manager agent."""
from ..models import AgentRole
from .base import BaseAgent


class ReleaseAgent(BaseAgent):
    role = AgentRole.RELEASE
    name = "Release Mgr"
    emoji = "🚀"

    def system_prompt(self) -> str:
        return (
            "You are the release manager. You are the final checkpoint before shipping. "
            "You review all prior agent outputs and produce a release summary: "
            "what is shipping, what was deferred, known issues, rollback plan, "
            "and the PR description. "
            "You verify that: QA approved, security approved, docs are present. "
            "If anything critical is missing, set approved=false and list blockers. "
            "Your artifacts must include: 'pr_description' (full GitHub PR body in Markdown), "
            "'release_notes' (user-facing changelog), "
            "'rollback_plan' (steps to revert if production breaks), "
            "and 'checklist' (shipped / deferred / blocked items). "
            "next_roles should be empty — you are the last agent."
        )
