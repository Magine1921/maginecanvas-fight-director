#!/usr/bin/env python3
"""Validate a generated neutral MagineCanvas plan JSON."""
import json
import sys
from pathlib import Path
from build_node_plan import validate_plan, PlanError

def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/validate_node_plan.py plan.json")
    try:
        plan = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        validate_plan(plan)
        print(f"Valid: {len(plan['shots'])} shots, {len(plan['workflow']['nodes'])} nodes")
    except (ValueError, OSError, TypeError) as exc:
        raise SystemExit(f"Invalid plan: {exc}")

if __name__ == "__main__":
    main()
