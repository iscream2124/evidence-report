---
name: evidence-report
description: Research a consequential question from official primary sources, verify page-level evidence, produce and visually validate a final DOCX report, and optionally open and ingest it. Use for policy, grant, procurement, legal, compliance, or business reports where the user expects an evidence-backed deliverable rather than a quick answer.
---

# Evidence Report

Complete the evidence workflow without requiring the user to prompt each stage separately.

## Scope

Treat the user's requested subject, organizations, dates, output location, and requested mutations as the boundary. Research and local document creation are in scope. Publishing, submitting forms, sending messages, or modifying external systems requires explicit authorization.

## Workflow

1. Define the decision the report must support and the claims that require proof.
2. Find official primary sources first. Prefer the responsible agency, legislation, standards body, original dataset, or issuer of the notice.
3. Download the actual attachments when a page references a notice, guideline, Q&A, contract, or PDF. Do not treat the landing-page summary as the document.
   - When the bundled CLI is available, initialize a run with `evidence-report init`, preserve sources with `evidence-report add-source`, and extract PDFs with `evidence-report extract`.
4. Extract evidence with the document title, page, section or question number, date, and canonical URL. Visually inspect pages containing decisive tables or conditions.
   - Register decisive claims with `evidence-report add-evidence`; do not edit `evidence.json` by hand unless the CLI is unavailable.
5. Cross-check decisive claims. Separate:
   - confirmed facts;
   - reasoned interpretations;
   - unresolved questions.
6. Write the report for the user's decision. Do not convert a total program budget into a per-project cap, or absence of an explicit prohibition into guaranteed eligibility.
7. When DOCX is requested or implied by a final business report, generate it and render every page to images. Fix clipping, broken tables, missing glyphs, awkward page breaks, and unreadable citations.
8. Open the final deliverable when the user asks for a local handoff. Ingest only when the user requests it or project instructions make ingestion part of the requested workflow.
9. Run `evidence-report verify RUN_DIR` or `scripts/check_completion.py` against the run-state file. Do not claim completion unless it passes.

Read [references/source-policy.md](references/source-policy.md) when source authority or claim status is disputed. Read [references/completion-gates.md](references/completion-gates.md) before final delivery.

## Deliverables

Keep source files immutable. Store downloaded evidence, the final report, and a machine-readable `run-state.json` with stable paths. Provide clickable paths and a concise list of confirmed conclusions and remaining blockers.

If an official source cannot be obtained, label the report incomplete and state exactly what is missing. Never silently substitute a secondary summary.
