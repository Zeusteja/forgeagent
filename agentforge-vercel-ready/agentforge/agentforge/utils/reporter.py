"""Saves sprint outputs to disk."""
from __future__ import annotations
import json
import os
from datetime import datetime
from ..models import AgentOutput


def save_sprint(
    outputs: list[AgentOutput],
    title: str,
    output_dir: str = "sprint_outputs",
) -> str:
    """Write a sprint to markdown + JSON. Returns path to markdown file."""
    os.makedirs(output_dir, exist_ok=True)
    slug = title.lower().replace(" ", "_")[:40]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = os.path.join(output_dir, f"{ts}_{slug}")

    # --- Markdown report ---
    lines = [f"# Sprint Report: {title}", f"\n*Generated: {datetime.now().isoformat()}*\n", "---\n"]
    for out in outputs:
        lines.append(f"## {out.role.value.upper()} — {out.role.value.title()}")
        lines.append(f"\n**Approved:** {'✅' if out.approved else '❌'}\n")
        lines.append(f"**Summary:**\n{out.summary}\n")
        for name, content in out.artifacts.items():
            lines.append(f"### {name.replace('_', ' ').title()}")
            lines.append(f"\n```\n{content}\n```\n")
        lines.append("---\n")

    md_path = base + ".md"
    with open(md_path, "w") as f:
        f.write("\n".join(lines))

    # --- JSON dump ---
    data = [
        {
            "role": o.role.value,
            "approved": o.approved,
            "summary": o.summary,
            "artifacts": o.artifacts,
            "next_roles": [r.value for r in o.next_roles],
        }
        for o in outputs
    ]
    with open(base + ".json", "w") as f:
        json.dump({"title": title, "outputs": data}, f, indent=2)

    return md_path
