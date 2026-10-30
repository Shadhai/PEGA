"""Export the CINT-70 LangGraph workflow without starting runtime components.

Usage:
    .\venv\Scripts\python.exe generate_langgraph_diagram.py

The Mermaid output can be pasted into https://mermaid.live or previewed with a
Mermaid-compatible VS Code extension.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.agent.orchestrator import CINT70Orchestrator


def build_graph(domain: str):
    """Build the workflow topology without loading models or databases."""
    # _build_graph only registers bound callbacks and does not execute them.
    # Avoiding __init__ keeps diagram generation deterministic and lightweight.
    orchestrator = object.__new__(CINT70Orchestrator)
    orchestrator.domain = domain
    return orchestrator._build_graph().compile().get_graph()


def main() -> None:
    parser = argparse.ArgumentParser(description="Export the CINT-70 LangGraph topology")
    parser.add_argument(
        "--domain",
        choices=("space", "industrial"),
        default="space",
        help="Workflow domain label to include in the output filename",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("docs"),
        help="Directory for Mermaid and JSON output",
    )
    args = parser.parse_args()

    graph = build_graph(args.domain)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    mermaid_path = args.output_dir / f"cint70-{args.domain}-langgraph.mmd"
    json_path = args.output_dir / f"cint70-{args.domain}-langgraph.json"

    mermaid_path.write_text(graph.draw_mermaid(), encoding="utf-8")
    json_path.write_text(
        json.dumps(graph.to_json(), indent=2),
        encoding="utf-8",
    )

    print(f"Mermaid diagram: {mermaid_path}")
    print(f"Graph topology:  {json_path}")


if __name__ == "__main__":
    main()
