#!/usr/bin/env python3
"""Validate Evidence Report completion gates from a run-state JSON file."""

import json
import sys
from pathlib import Path

REQUIRED = (
    "official_sources_secured",
    "page_level_evidence_recorded",
    "critical_pages_visually_checked",
    "claim_states_separated",
    "material_numbers_cross_checked",
    "final_deliverable_created",
    "deliverable_openable",
)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: check_completion.py RUN_STATE.json", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"invalid run state: {exc}", file=sys.stderr)
        return 2
    required = list(REQUIRED)
    if state.get("docx_required", False):
        required.append("all_docx_pages_rendered_and_checked")
    if state.get("ingest_required", False):
        required.append("ingest_completed")
    failed = [key for key in required if state.get(key) is not True]
    if failed:
        print("INCOMPLETE: " + ", ".join(failed))
        return 1
    print("COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
