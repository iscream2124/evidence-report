# Evidence Report

Evidence Report is a portable Agent Skill for turning consequential research requests into official-source, page-verified, visually checked DOCX reports.

It is designed for Codex and Claude-compatible Agent Skills. The same `SKILL.md`, references, and deterministic completion checker are shared by both environments.

## What it prevents

- stopping at a search-result summary;
- treating a total budget as a per-project cap;
- claiming eligibility from the absence of a prohibition;
- citing a PDF without opening the decisive page;
- delivering a DOCX without rendering every page;
- calling a run complete while requested archival work remains.

## Install

```bash
git clone https://github.com/iscream2124/evidence-report.git
cd evidence-report
./install.sh
```

The installer links the skill into:

- `~/.agents/skills/evidence-report` for Codex;
- `~/.claude/skills/evidence-report` for Claude-compatible Agent Skills.

## Use

In Codex:

```text
$evidence-report Research whether a mid-sized company can join the cooking-robot demonstration program. Finish the official evidence, DOCX, visual QA, and local handoff.
```

Natural-language invocation also works when the agent supports implicit skill discovery.

## Completion gate

Create a run-state file from `examples/run-state.example.json`, then run:

```bash
python3 skills/evidence-report/scripts/check_completion.py run-state.json
```

The command exits with status 1 until all applicable gates pass.

## Portability

The workflow is expressed as an Agent Skill. Platform-specific UI metadata lives in `agents/openai.yaml`; the core instructions, references, and scripts remain platform-neutral. An MCP server can be added later for hosted source acquisition and document rendering without changing the skill contract.

## License

Apache-2.0
