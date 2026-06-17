"""Pipeline orchestrator: routes tasks between agents."""
from __future__ import annotations
import uuid
from typing import Optional
from ..models import Task, AgentOutput, AgentRole
from ..agents import (
    CEOAgent, ArchitectAgent, EngineerAgent, DesignerAgent,
    QAAgent, SecurityAgent, DocsAgent, ReleaseAgent,
)

# Map role → agent instance
REGISTRY: dict[AgentRole, object] = {
    AgentRole.CEO: CEOAgent(),
    AgentRole.ARCHITECT: ArchitectAgent(),
    AgentRole.ENGINEER: EngineerAgent(),
    AgentRole.DESIGNER: DesignerAgent(),
    AgentRole.QA: QAAgent(),
    AgentRole.SECURITY: SecurityAgent(),
    AgentRole.DOCS: DocsAgent(),
    AgentRole.RELEASE: ReleaseAgent(),
}

# The default sprint order when the user just says "run"
DEFAULT_PIPELINE: list[AgentRole] = [
    AgentRole.CEO,
    AgentRole.ARCHITECT,
    AgentRole.ENGINEER,
    AgentRole.QA,
    AgentRole.SECURITY,
    AgentRole.DOCS,
    AgentRole.RELEASE,
]

MAX_LOOPS = 2  # max times a role can be re-run (to handle QA→engineer→QA cycles)


class Pipeline:
    def __init__(self, verbose: bool = True, on_agent_done=None):
        self.verbose = verbose
        self.on_agent_done = on_agent_done  # callback(agent, output)
        self.outputs: list[AgentOutput] = []

    def run(
        self,
        title: str,
        description: str,
        start_role: Optional[AgentRole] = None,
        pipeline: Optional[list[AgentRole]] = None,
    ) -> list[AgentOutput]:
        """Run a full sprint. Returns all agent outputs in order."""
        self.outputs = []
        run_counts: dict[AgentRole, int] = {}

        task_id = str(uuid.uuid4())[:8]

        # Initial queue
        if pipeline:
            queue = list(pipeline)
        elif start_role:
            queue = [start_role]
        else:
            queue = list(DEFAULT_PIPELINE)

        history: list[dict] = []

        while queue:
            role = queue.pop(0)
            run_counts[role] = run_counts.get(role, 0) + 1

            if run_counts[role] > MAX_LOOPS:
                self._log(f"⚠️  Skipping {role.value} — loop limit reached.")
                continue

            agent = REGISTRY[role]
            self._log(f"\n{agent.emoji}  [{agent.name}] thinking…")

            task = Task(
                id=f"{task_id}-{role.value}",
                title=title,
                description=description,
                role=role,
                history=list(history),
            )

            output = agent.run(task)
            self.outputs.append(output)

            # Snapshot for history
            history.append({
                "role": output.role.value,
                "summary": output.summary,
                "artifacts": output.artifacts,
                "approved": output.approved,
            })

            if self.on_agent_done:
                self.on_agent_done(agent, output)

            self._log(f"   ✓ {output.summary[:120]}{'…' if len(output.summary) > 120 else ''}")

            if not output.approved:
                self._log(f"   ⛔ {agent.name} did NOT approve — re-routing.")

            # Prepend suggested next roles (don't duplicate what's already queued)
            queued_set = set(queue)
            for next_role in reversed(output.next_roles):
                if next_role not in queued_set:
                    queue.insert(0, next_role)
                    queued_set.add(next_role)

        return self.outputs

    def _log(self, msg: str):
        if self.verbose:
            print(msg)
