# 🤖 AgentForge

**A self-routing multi-agent AI team — built as a standalone Python CLI deployable to any GitHub repo.**

One idea → 8 specialist AI agents → full sprint output (spec, architecture, code review, test plan, security audit, docs, PR description) — all in one command.

```
agentforge sprint "User Auth" "Email+password login with JWT, rate limiting, and Google OAuth."
```

---

## What it is

AgentForge gives you a complete virtual engineering team powered by Claude. Each agent has a specific role and passes structured output to the next. They route themselves — you don't have to decide who reviews what.

| Agent | Role | What they produce |
|-------|------|-------------------|
| 🎯 CEO | Product Strategy | Product spec, success criteria, scope decisions |
| 🏗️ Architect | Technical Design | Architecture, data models, API contracts, tech stack |
| 👩‍💻 Engineer | Implementation | Code, unit tests, implementation notes |
| 🎨 Designer | UX/UI | User flows, design tokens, accessibility notes |
| 🧪 QA Lead | Quality Assurance | Test plan, bugs found (blocks on critical), regression tests |
| 🔒 Security | Security Audit | OWASP Top-10 + STRIDE threat model, verdict |
| 📝 Tech Writer | Documentation | README, how-to guide, changelog entry |
| 🚀 Release Mgr | Ship Readiness | PR description, release notes, rollback plan, checklist |

**Self-routing:** agents decide who runs next based on what they found. A QA agent that finds critical bugs routes back to the engineer. A security agent that finds a critical vuln blocks release. A CEO who decides UX needs work routes to the designer before the architect.

---

## Quick start

```bash
# 1. Clone
git clone https://github.com/your-username/agentforge
cd agentforge

# 2. Install
pip install -e .

# 3. Add your API key
export ANTHROPIC_API_KEY=sk-ant-...

# 4. Run a sprint
agentforge sprint "Feature name" "Detailed description of what you want to build."
```

The report is saved to `sprint_outputs/` as both `.md` and `.json`.

---

## CLI reference

### `agentforge sprint`

Run a full team sprint.

```bash
agentforge sprint TITLE DESCRIPTION [options]

Options:
  --agents / -a   Override which agents run (in order)
                  Choices: ceo architect engineer designer qa security docs release
  --start / -s    Start with one agent and let it route the rest
  --output-dir    Where to save reports (default: sprint_outputs/)
  --no-save       Don't write to disk
```

**Examples:**

```bash
# Full default pipeline (ceo → architect → engineer → qa → security → docs → release)
agentforge sprint "Payment integration" "Add Stripe checkout to our SaaS app."

# Skip to code review agents only
agentforge sprint "Hotfix review" "Race condition in session store" \
  --agents qa security

# Let the CEO decide everything
agentforge sprint "New product idea" "Build an AI-powered recipe generator" \
  --start ceo

# Custom pipeline
agentforge sprint "API redesign" "Move to GraphQL" \
  --agents ceo architect security docs
```

### `agentforge agent`

Run a single agent in isolation.

```bash
agentforge agent ROLE TITLE DESCRIPTION
```

```bash
# Just a security audit
agentforge agent security "Auth module audit" "Review our JWT implementation."
```

### `agentforge list`

Show all available agents and the default pipeline.

```bash
agentforge list
```

---

## Python API

Use AgentForge as a library in your own scripts:

```python
from agentforge.pipeline import Pipeline
from agentforge.models import AgentRole
from agentforge.utils import save_sprint

pipeline = Pipeline(verbose=True)

outputs = pipeline.run(
    title="User Authentication",
    description="Email + password login with JWT sessions.",
    pipeline=[AgentRole.CEO, AgentRole.ARCHITECT, AgentRole.SECURITY],
)

path = save_sprint(outputs, "User Authentication")
print(f"Report: {path}")
```

Each `AgentOutput` has:
- `role` — which agent ran
- `summary` — what they did
- `artifacts` — named output blobs (spec, code, test_plan, etc.)
- `approved` — whether they signed off
- `next_roles` — who they recommend runs next

---

## GitHub Actions

### CI (always on)
`.github/workflows/ci.yml` runs tests on every push and PR.

### Sprint on PR (optional)
`.github/workflows/sprint_on_pr.yml` runs an architect + engineer + QA + security review on every PR and posts the result as a comment.

**To enable:** add `ANTHROPIC_API_KEY` as a repository secret in GitHub → Settings → Secrets.

---

## Deploying to Vercel

AgentForge ships as two pieces — a Python (FastAPI) backend at the repo root and a Next.js frontend in `frontend/` — and the most reliable way to run both on Vercel is as **two separate Vercel projects** pointed at the same GitHub repo. (Combining a Python function and a Next.js app into a single Vercel project via one `vercel.json` is fragile in practice; separate projects with their own Root Directory are the supported, zero-config path.)

### 1. Deploy the API

- In Vercel, **Add New → Project**, import this repo, and leave **Root Directory** as `/` (the repo root).
- Vercel auto-detects the Python runtime from `requirements.txt` and `api/index.py` — no extra config needed.
- Add an environment variable: `ANTHROPIC_API_KEY` = your Anthropic API key.
- Optionally add `FRONTEND_ORIGIN` = your frontend's deployed URL (step 2) to lock down CORS instead of allowing all origins.
- Deploy. Your API will be live at `https://<api-project>.vercel.app`, with a health check at `/` and the sprint endpoint at `/chat`.

### 2. Deploy the frontend

- **Add New → Project** again, import the same repo, but set **Root Directory** to `frontend`.
- Vercel auto-detects Next.js.
- Add an environment variable: `NEXT_PUBLIC_API_URL` = the URL from step 1 (e.g. `https://agentforge-api.vercel.app`).
- Deploy. Your UI will be live at `https://<frontend-project>.vercel.app`.

Both projects redeploy automatically on every push to `main`.

---

## How it differs from gstack

| | gstack | AgentForge |
|--|--------|------------|
| Interface | Claude Code slash-commands | Python CLI + importable library |
| Requires | Claude Code installed | `pip install` + API key |
| Routing | Fixed sprint pipeline | Self-routing (agents decide next steps) |
| CI integration | Manual | GitHub Actions built-in |
| Language | TypeScript | Python |
| State | File-based per-session | Structured JSON + Markdown |
| Loop guard | Manual | Automatic (MAX_LOOPS = 2) |

gstack is a power tool for Claude Code users. AgentForge is for teams that want a standalone, scriptable, CI-integrated multi-agent system.

---

## Adding a custom agent

```python
# myagents/legal.py
from agentforge.agents.base import BaseAgent
from agentforge.models import AgentRole

class LegalAgent(BaseAgent):
    role = AgentRole.DOCS   # reuse closest role, or extend AgentRole
    name = "Legal Reviewer"
    emoji = "⚖️"

    def system_prompt(self):
        return "You are a legal reviewer. Check for IP, licensing, and compliance issues..."
```

Register it in the pipeline:

```python
from agentforge.pipeline import REGISTRY
from agentforge.models import AgentRole
from myagents.legal import LegalAgent

REGISTRY[AgentRole.DOCS] = LegalAgent()
```

---

## Running tests

```bash
pip install pytest
pytest tests/ -v
```

All tests are offline — they mock the Anthropic API. No API key needed for testing.

---

## Project structure

```
agentforge/
├── agentforge/
│   ├── agents/         # One file per specialist agent
│   │   ├── base.py     # BaseAgent (shared run logic + JSON parsing)
│   │   ├── ceo.py
│   │   ├── architect.py
│   │   ├── engineer.py
│   │   ├── designer.py
│   │   ├── qa.py
│   │   ├── security.py
│   │   ├── docs.py
│   │   └── release.py
│   ├── pipeline/
│   │   └── orchestrator.py   # Routes tasks between agents
│   ├── utils/
│   │   └── reporter.py       # Saves sprint to .md + .json
│   ├── api.py          # Anthropic API wrapper
│   ├── cli.py          # CLI (argparse)
│   └── models.py       # Task, AgentOutput, AgentRole
├── .github/workflows/
│   ├── ci.yml
│   └── sprint_on_pr.yml
├── examples/
│   └── example_sprint.py
├── tests/
│   └── test_agentforge.py
├── pyproject.toml
└── README.md
```

---

## License

MIT — free forever.
