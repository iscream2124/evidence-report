from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core import (add_evidence, add_source, completion_failures, create_run,
                   extract_pdfs, read_json, update_state)


def run_dir(value: str) -> Path:
    path = Path(value).expanduser().resolve()
    if not (path / "qa/run-state.json").is_file():
        raise argparse.ArgumentTypeError(f"not an Evidence Report run: {path}")
    return path


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="evidence-report")
    root.add_argument("--version", action="version", version="evidence-report 0.2.2")
    commands = root.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init", help="create a new evidence run")
    init.add_argument("--topic", required=True)
    init.add_argument("--output", type=Path, default=Path("runs"))

    source = commands.add_parser("add-source", help="download or copy a source")
    source.add_argument("run", type=run_dir)
    source.add_argument("source")
    source.add_argument("--official", action="store_true")

    extract = commands.add_parser("extract", help="extract text from PDF sources")
    extract.add_argument("run", type=run_dir)

    evidence = commands.add_parser("add-evidence", help="register a page-level claim")
    evidence.add_argument("run", type=run_dir)
    evidence.add_argument("--claim", required=True)
    evidence.add_argument("--status", required=True,
                          choices=["confirmed", "corroborated", "interpreted", "unresolved", "conflicted"])
    evidence.add_argument("--source-id", required=True)
    evidence.add_argument("--page", type=int)
    evidence.add_argument("--section", default="")
    evidence.add_argument("--quote", default="")

    state = commands.add_parser("set-state", help="update a completion gate")
    state.add_argument("run", type=run_dir)
    state.add_argument("key")
    state.add_argument("value", choices=["true", "false"])

    status = commands.add_parser("status", help="print run state")
    status.add_argument("run", type=run_dir)

    verify = commands.add_parser("verify", help="check deterministic completion gates")
    verify.add_argument("run", type=run_dir)

    execute = commands.add_parser("run", help="create a run, add one source, and extract PDFs")
    execute.add_argument("--topic", required=True)
    execute.add_argument("--source", required=True)
    execute.add_argument("--output", type=Path, default=Path("runs"))
    execute.add_argument("--official", action="store_true")
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "init":
            result = create_run(args.topic, args.output.expanduser().resolve())
            print(result)
        elif args.command == "add-source":
            print(json.dumps(add_source(args.run, args.source, args.official), ensure_ascii=False, indent=2))
        elif args.command == "extract":
            print(json.dumps(extract_pdfs(args.run), ensure_ascii=False, indent=2))
        elif args.command == "add-evidence":
            print(json.dumps(add_evidence(args.run, claim=args.claim, status=args.status,
                                          source_id=args.source_id, page=args.page,
                                          section=args.section, quote=args.quote),
                             ensure_ascii=False, indent=2))
        elif args.command == "set-state":
            print(json.dumps(update_state(args.run, args.key, args.value == "true"), indent=2))
        elif args.command == "status":
            print(json.dumps(read_json(args.run / "qa/run-state.json"), ensure_ascii=False, indent=2))
        elif args.command == "verify":
            failures = completion_failures(read_json(args.run / "qa/run-state.json"))
            if failures:
                print("INCOMPLETE: " + ", ".join(failures))
                return 1
            print("COMPLETE")
        elif args.command == "run":
            result = create_run(args.topic, args.output.expanduser().resolve())
            add_source(result, args.source, args.official)
            extract_pdfs(result)
            print(result)
        return 0
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
