"""Shared data models for AgentForge."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class AgentRole(str, Enum):
    CEO = "ceo"
    ARCHITECT = "architect"
    ENGINEER = "engineer"
    DESIGNER = "designer"
    QA = "qa"
    SECURITY = "security"
    DOCS = "docs"
    RELEASE = "release"


@dataclass
class Task:
    """A unit of work passed between agents."""
    id: str
    title: str
    description: str
    role: AgentRole
    context: dict = field(default_factory=dict)
    history: list[dict] = field(default_factory=list)  # prior agent outputs


@dataclass
class AgentOutput:
    """What an agent produces after processing a task."""
    role: AgentRole
    summary: str
    artifacts: dict = field(default_factory=dict)   # named string blobs (e.g. spec, tests, release-notes)
    next_roles: list[AgentRole] = field(default_factory=list)  # who should run next
    approved: bool = True
    raw: str = ""
