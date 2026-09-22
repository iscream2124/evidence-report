from __future__ import annotations

import hashlib
import json
import re
import shutil
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from pypdf import PdfReader


STATE_DEFAULTS = {
    "official_sources_secured": False,
    "page_level_evidence_recorded": False,
    "critical_pages_visually_checked": False,
    "claim_states_separated": False,
    "material_numbers_cross_checked": False,
    "final_deliverable_created": False,
    "deliverable_openable": False,
    "docx_required": False,
    "all_docx_pages_rendered_and_checked": False,
    "ingest_required": False,
    "ingest_completed": False,
}

BASE_REQUIRED_GATES = (
    "official_sources_secured",
    "page_level_evidence_recorded",
    "critical_pages_visually_checked",
    "claim_states_separated",
    "material_numbers_cross_checked",
    "final_deliverable_created",
    "deliverable_openable",
)


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^\w가-힣]+", "-", value, flags=re.UNICODE)
    return value.strip("-") or "evidence-run"


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def create_run(topic: str, output: Path) -> Path:
    run_dir = output / f"{date.today().isoformat()}-{slugify(topic)}"
    for child in ("sources/files", "evidence/pages", "report", "qa"):
        (run_dir / child).mkdir(parents=True, exist_ok=True)
    write_json(run_dir / "request.json", {
        "topic": topic,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "schema_version": "1.0",
    })
    write_json(run_dir / "sources/source-index.json", {"sources": []})
    write_json(run_dir / "evidence/evidence.json", {"claims": []})
    write_json(run_dir / "qa/run-state.json", dict(STATE_DEFAULTS))
    return run_dir


def _unique_target(directory: Path, name: str) -> Path:
    clean = re.sub(r"[^A-Za-z0-9._가-힣-]+", "-", name).strip("-") or "source"
    target = directory / clean
    index = 2
    while target.exists():
        target = directory / f"{Path(clean).stem}-{index}{Path(clean).suffix}"
        index += 1
    return target


def add_source(run_dir: Path, source: str, official: bool = False) -> dict[str, Any]:
    files_dir = run_dir / "sources/files"
    parsed = urllib.parse.urlparse(source)
    if parsed.scheme in {"http", "https"}:
        request = urllib.request.Request(source, headers={"User-Agent": "evidence-report/0.2"})
        with urllib.request.urlopen(request, timeout=60) as response:
            content_type = response.headers.get_content_type()
            disposition = response.headers.get("Content-Disposition", "")
            encoded = re.search(r"filename\*=UTF-8''([^;]+)", disposition, flags=re.I)
            plain = re.search(r'filename="?([^";]+)', disposition, flags=re.I)
            name = urllib.parse.unquote(encoded.group(1)) if encoded else (plain.group(1) if plain else "")
            if not name:
                name = Path(urllib.parse.unquote(parsed.path)).name or "downloaded-source"
            if content_type == "application/pdf" and not name.lower().endswith(".pdf"):
                name += ".pdf"
            target = _unique_target(files_dir, name)
            with target.open("wb") as out:
                shutil.copyfileobj(response, out)
        origin, source_type = source, "url"
    else:
        origin_path = Path(source).expanduser().resolve()
        if not origin_path.is_file():
            raise FileNotFoundError(origin_path)
        target = _unique_target(files_dir, origin_path.name)
        shutil.copy2(origin_path, target)
        origin, source_type, content_type = str(origin_path), "file", None
    index_path = run_dir / "sources/source-index.json"
    index = read_json(index_path)
    record = {
        "id": f"source-{len(index['sources']) + 1:03d}",
        "origin": origin,
        "source_type": source_type,
        "official": official,
        "local_path": str(target.relative_to(run_dir)),
        "filename": target.name,
        "content_type": content_type,
        "bytes": target.stat().st_size,
        "sha256": sha256(target),
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }
    index["sources"].append(record)
    write_json(index_path, index)
    state_path = run_dir / "qa/run-state.json"
    state = read_json(state_path)
    state["official_sources_secured"] = any(s.get("official") for s in index["sources"])
    write_json(state_path, state)
    return record


def extract_pdfs(run_dir: Path) -> list[dict[str, Any]]:
    index = read_json(run_dir / "sources/source-index.json")
    extracted = []
    for source in index["sources"]:
        path = run_dir / source["local_path"]
        with path.open("rb") as stream:
            pdf_magic = stream.read(5) == b"%PDF-"
        if path.suffix.lower() != ".pdf" and source.get("content_type") != "application/pdf" and not pdf_magic:
            continue
        reader = PdfReader(str(path))
        pages = []
        for number, page in enumerate(reader.pages, 1):
            text = page.extract_text() or ""
            page_file = run_dir / "evidence/pages" / f"{source['id']}-page-{number:04d}.txt"
            page_file.write_text(text, encoding="utf-8")
            pages.append({
                "page": number,
                "text_path": str(page_file.relative_to(run_dir)),
                "characters": len(text),
            })
        source["pdf"] = {"pages": len(pages), "extracted_pages": pages}
        extracted.append({"source_id": source["id"], "pages": len(pages)})
    write_json(run_dir / "sources/source-index.json", index)
    return extracted


def add_evidence(run_dir: Path, *, claim: str, status: str, source_id: str,
                 page: int | None = None, section: str = "", quote: str = "") -> dict[str, Any]:
    if status not in {"confirmed", "corroborated", "interpreted", "unresolved", "conflicted"}:
        raise ValueError(f"unsupported status: {status}")
    source_index = read_json(run_dir / "sources/source-index.json")
    source = next((item for item in source_index["sources"] if item["id"] == source_id), None)
    if source is None:
        raise ValueError(f"unknown source id: {source_id}")
    evidence_path = run_dir / "evidence/evidence.json"
    evidence = read_json(evidence_path)
    item = {
        "id": f"claim-{len(evidence['claims']) + 1:03d}",
        "claim": claim,
        "status": status,
        "source_id": source_id,
        "document": source["filename"],
        "page": page,
        "section": section,
        "quote": quote,
        "origin": source["origin"],
        "source_sha256": source["sha256"],
    }
    evidence["claims"].append(item)
    write_json(evidence_path, evidence)
    state_path = run_dir / "qa/run-state.json"
    state = read_json(state_path)
    state["page_level_evidence_recorded"] = any(c.get("page") for c in evidence["claims"])
    states = {c["status"] for c in evidence["claims"]}
    state["claim_states_separated"] = bool(states) and all(c.get("status") for c in evidence["claims"])
    write_json(state_path, state)
    return item


def update_state(run_dir: Path, key: str, value: bool) -> dict[str, Any]:
    state_path = run_dir / "qa/run-state.json"
    state = read_json(state_path)
    if key not in STATE_DEFAULTS:
        raise ValueError(f"unknown state key: {key}")
    state[key] = value
    write_json(state_path, state)
    return state


def completion_failures(state: dict[str, Any]) -> list[str]:
    required = list(BASE_REQUIRED_GATES)
    if state.get("docx_required", False):
        required.append("all_docx_pages_rendered_and_checked")
    if state.get("ingest_required", False):
        required.append("ingest_completed")
    return [key for key in required if state.get(key) is not True]
