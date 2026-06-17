"""AgentForge CLI."""
from __future__ import annotations
import argparse
import sys
import os

from .models import AgentRole
from .pipeline import Pipeline, DEFAULT_PIPELINE, REGISTRY
from .utils import save_sprint


ROLE_NAMES = [r.value for r in AgentRole]


def _print_banner():
    print("""
╔═══════════════════════════════════════════╗
║          🤖  A G E N T F O R G E         ║
║   Your AI virtual team, fully automated   ║
╚═══════════════════════════════════════════╝
""")


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="agentforge",
        description="Run a multi-agent AI sprint on any feature idea.",
    )
    sub = p.add_subparsers(dest="command")

    # ── sprint ──
    sprint = sub.add_parser("sprint", help="Run a full team sprint on a feature request.")
    sprint.add_argument("title", help="Short title of the feature or task.")
    sprint.add_argument(
        "description",
        help="Detailed description. Wrap in quotes.",
    )
    sprint.add_argument(
        "--agents", "-a",
        nargs="+",
        choices=ROLE_NAMES,
        metavar="ROLE",
        help=f"Override which agents run (order matters). Choices: {', '.join(ROLE_NAMES)}",
    )
    sprint.add_argument(
        "--start", "-s",
        choices=ROLE_NAMES,
        metavar="ROLE",
        help="Start with a single agent and let it route the rest.",
    )
    sprint.add_argument(
        "--output-dir", "-o",
        default="sprint_outputs",
        help="Directory for saved reports (default: sprint_outputs/).",
    )
    sprint.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save report to disk.",
    )

    # ── agent ──
    ag = sub.add_parser("agent", help="Run a single agent in isolation.")
    ag.add_argument("role", choices=ROLE_NAMES, help="Agent role to run.")
    ag.add_argument("title", help="Task title.")
    ag.add_argument("description", help="Task description.")
    ag.add_argument("--output-dir", "-o", default="sprint_outputs")
    ag.add_argument("--no-save", action="store_true")

    # ── list ──
    sub.add_parser("list", help="List all available agents.")

    return p


def main(argv=None) -> int:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("❌  ANTHROPIC_API_KEY is not set. Export it and re-run.", file=sys.stderr)
        return 1

    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        _print_banner()
        parser.print_help()
        return 0

    if args.command == "list":
        _print_banner()
        print("Available agents (roles):\n")
        for role in AgentRole:
            agent = REGISTRY[role]
            print(f"  {agent.emoji}  {role.value:<12}  {agent.name}")
        print(f"\nDefault pipeline: {' → '.join(r.value for r in DEFAULT_PIPELINE)}")
        return 0

    if args.command in ("sprint", "agent"):
        _print_banner()

        pipeline_roles = None
        start_role = None

        if args.command == "agent":
            pipeline_roles = [AgentRole(args.role)]
        elif args.agents:
            pipeline_roles = [AgentRole(r) for r in args.agents]
        elif args.start:
            start_role = AgentRole(args.start)

        print(f"📋  Task: {args.title}")
        print(f"📝  Description: {args.description[:80]}{'…' if len(args.description) > 80 else ''}\n")

        pipeline = Pipeline(verbose=True)
        outputs = pipeline.run(
            title=args.title,
            description=args.description,
            pipeline=pipeline_roles,
            start_role=start_role,
        )

        # Final summary
        print("\n" + "═" * 50)
        print("SPRINT COMPLETE")
        print("═" * 50)
        approved = all(o.approved for o in outputs)
        print(f"Overall status: {'✅ APPROVED' if approved else '❌ BLOCKED'}")
        for o in outputs:
            status = "✅" if o.approved else "❌"
            print(f"  {status} {o.role.value:<12} — {o.summary[:80]}")

        if not args.no_save:
            path = save_sprint(outputs, args.title, args.output_dir)
            print(f"\n📁  Report saved to: {path}")

        return 0 if approved else 2

    return 0
