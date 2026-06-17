"""Abstract base agent."""
from __future__ import annotations
import json
from abc import ABC, abstractmethod
from ..models import Task, AgentOutput, AgentRole
from ..api import chat


class BaseAgent(ABC):
    role: AgentRole
    name: str
    emoji: str

    @abstractmethod
    def system_prompt(self) -> str:
        ...

    def run(self, task: Task) -> AgentOutput:
        history_block = ""
        if task.history:
            history_block = "\n\n---\nPREVIOUS AGENT OUTPUTS:\n"
            for h in task.history:
                history_block += f"\n### {h['role'].upper()}\n{h['summary']}\n"
                for k, v in h.get("artifacts", {}).items():
                    history_block += f"\n**{k}:**\n{v}\n"

        user_msg = (
            f"TASK: {task.title}\n\nDESCRIPTION:\n{task.description}"
            + history_block
            + "\n\n---\nRespond with a JSON object using this exact schema:\n"
            "{\n"
            '  "summary": "concise summary of your work",\n'
            '  "artifacts": {"<artifact_name>": "<content>", ...},\n'
            '  "next_roles": ["<role1>", "<role2>"],\n'  
            '  "approved": true\n'
            "}\n"
            "next_roles must be a subset of: ceo, architect, engineer, designer, qa, security, docs, release.\n"
            "Return ONLY the JSON object — no markdown fences, no preamble."
        )

        raw = chat(self.system_prompt(), user_msg, max_tokens=3000)

        try:
            # strip possible markdown fences
            clean = raw.strip()
            if clean.startswith("```"):
                clean = "\n".join(clean.split("\n")[1:])
            if clean.endswith("```"):
                clean = "\n".join(clean.split("\n")[:-1])
            data = json.loads(clean)
        except json.JSONDecodeError:
            # graceful degradation: treat entire text as summary
            data = {"summary": raw, "artifacts": {}, "next_roles": [], "approved": True}

        next_roles = [AgentRole(r) for r in data.get("next_roles", []) if r in AgentRole._value2member_map_]

        return AgentOutput(
            role=self.role,
            summary=data.get("summary", ""),
            artifacts=data.get("artifacts", {}),
            next_roles=next_roles,
            approved=data.get("approved", True),
            raw=raw,
        )
