"""Unit tests — all offline (no API calls)."""
import json
import pytest
from unittest.mock import patch, MagicMock

from agentforge.models import Task, AgentOutput, AgentRole
from agentforge.agents.base import BaseAgent
from agentforge.agents.ceo import CEOAgent
from agentforge.agents.qa import QAAgent
from agentforge.pipeline.orchestrator import Pipeline, DEFAULT_PIPELINE
from agentforge.utils.reporter import save_sprint


# ── Helpers ──────────────────────────────────────────────────────────────────

def make_task(role=AgentRole.CEO):
    return Task(
        id="test-001",
        title="Test feature",
        description="A simple test.",
        role=role,
    )


def mock_api_response(role: AgentRole, next_roles=None, approved=True):
    """Return a valid JSON string an agent would produce."""
    return json.dumps({
        "summary": f"Done as {role.value}",
        "artifacts": {"spec": "some content"},
        "next_roles": [r.value for r in (next_roles or [])],
        "approved": approved,
    })


# ── Model tests ───────────────────────────────────────────────────────────────

def test_agent_role_values():
    assert AgentRole.CEO.value == "ceo"
    assert AgentRole.RELEASE.value == "release"


def test_task_defaults():
    t = make_task()
    assert t.history == []
    assert t.context == {}


def test_agent_output_defaults():
    out = AgentOutput(role=AgentRole.QA, summary="ok")
    assert out.approved is True
    assert out.next_roles == []


# ── Agent tests ───────────────────────────────────────────────────────────────

@patch("agentforge.agents.base.chat")
def test_ceo_agent_run(mock_chat):
    mock_chat.return_value = mock_api_response(AgentRole.CEO, next_roles=[AgentRole.ARCHITECT])
    agent = CEOAgent()
    output = agent.run(make_task(AgentRole.CEO))
    assert output.role == AgentRole.CEO
    assert output.approved is True
    assert AgentRole.ARCHITECT in output.next_roles
    assert "spec" in output.artifacts


@patch("agentforge.agents.base.chat")
def test_qa_agent_blocks_on_critical_bug(mock_chat):
    mock_chat.return_value = json.dumps({
        "summary": "Found critical bugs",
        "artifacts": {"bugs_found": "SQL injection in login"},
        "next_roles": ["engineer"],
        "approved": False,
    })
    agent = QAAgent()
    output = agent.run(make_task(AgentRole.QA))
    assert output.approved is False
    assert AgentRole.ENGINEER in output.next_roles


@patch("agentforge.agents.base.chat")
def test_agent_graceful_on_bad_json(mock_chat):
    mock_chat.return_value = "Oops, here is some plain text response"
    agent = CEOAgent()
    output = agent.run(make_task(AgentRole.CEO))
    assert output.role == AgentRole.CEO
    assert "Oops" in output.summary  # raw text used as summary


# ── Pipeline tests ────────────────────────────────────────────────────────────

@patch("agentforge.agents.base.chat")
def test_pipeline_runs_default_order(mock_chat):
    def side_effect(system, user, **kwargs):
        # Each agent says done, no next roles
        return json.dumps({"summary": "done", "artifacts": {}, "next_roles": [], "approved": True})
    mock_chat.side_effect = side_effect

    p = Pipeline(verbose=False)
    outputs = p.run("Test", "description", pipeline=list(DEFAULT_PIPELINE))
    roles = [o.role for o in outputs]
    assert roles == list(DEFAULT_PIPELINE)


@patch("agentforge.agents.base.chat")
def test_pipeline_respects_custom_order(mock_chat):
    mock_chat.return_value = json.dumps({"summary": "done", "artifacts": {}, "next_roles": [], "approved": True})
    p = Pipeline(verbose=False)
    custom = [AgentRole.QA, AgentRole.SECURITY]
    outputs = p.run("T", "D", pipeline=custom)
    assert [o.role for o in outputs] == custom


@patch("agentforge.agents.base.chat")
def test_pipeline_prevents_infinite_loop(mock_chat):
    # QA always says "go back to engineer" — loop guard should kick in
    def side_effect(system, user, **kwargs):
        return json.dumps({"summary": "needs fix", "artifacts": {}, "next_roles": ["engineer"], "approved": False})
    mock_chat.side_effect = side_effect

    p = Pipeline(verbose=False)
    outputs = p.run("T", "D", pipeline=[AgentRole.ENGINEER, AgentRole.QA])
    engineer_runs = sum(1 for o in outputs if o.role == AgentRole.ENGINEER)
    assert engineer_runs <= 2  # MAX_LOOPS


@patch("agentforge.agents.base.chat")
def test_pipeline_callback_called(mock_chat):
    mock_chat.return_value = json.dumps({"summary": "ok", "artifacts": {}, "next_roles": [], "approved": True})
    called = []
    p = Pipeline(verbose=False, on_agent_done=lambda agent, out: called.append(out.role))
    p.run("T", "D", pipeline=[AgentRole.CEO])
    assert AgentRole.CEO in called


# ── Reporter tests ────────────────────────────────────────────────────────────

def test_save_sprint(tmp_path):
    outputs = [
        AgentOutput(role=AgentRole.CEO, summary="CEO done", artifacts={"product_spec": "spec here"}),
        AgentOutput(role=AgentRole.RELEASE, summary="Shipped", artifacts={"pr_description": "# PR"}),
    ]
    md_path = save_sprint(outputs, "My Feature", output_dir=str(tmp_path))
    assert md_path.endswith(".md")
    content = open(md_path).read()
    assert "CEO" in content
    assert "spec here" in content
    # JSON also written
    import os
    json_files = [f for f in os.listdir(tmp_path) if f.endswith(".json")]
    assert len(json_files) == 1
