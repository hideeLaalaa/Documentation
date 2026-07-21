from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from .generate import generate
from .models import load_document
from .paths import documents_root, index_path


def discover_documents() -> list[Path]:
    """Find Phase 3 JSON sources (SA-*.json), skipping templates and drafts."""
    found = []
    for path in sorted(documents_root().rglob("SA-*.json")):
        if path.name.startswith("_"):
            continue
        if path.name.lower() == "schema.json":
            continue
        found.append(path)
    return found


def rebuild_index() -> dict:
    docs = []
    for path in discover_documents():
        document = load_document(path)
        docs.append(document.to_index_entry())

    docs.sort(key=lambda d: d["number"])
    payload = {
        "project": "Spotlight Advocate Documentation System",
        "updated": date.today().isoformat(),
        "documents": docs,
    }
    with open(index_path(), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")
    return payload


def rebuild_library(*, make_pdf: bool = True, validate_first: bool = True) -> dict:
    """
    Phase 8: one-click rebuild of the entire library from JSON + gold master.
    """
    if validate_first:
        from .library import validate_library

        report = validate_library()
        if not report["ok"]:
            failed = [d for d in report["documents"] if not d["ok"]]
            details = []
            for item in failed:
                details.append(
                    f"{item['number']}: " + "; ".join(item["errors"])
                )
            raise ValueError(
                "Rebuild aborted — fix validation errors first:\n  - "
                + "\n  - ".join(details)
            )

    index = rebuild_index()
    results = []
    for entry in index["documents"]:
        result = generate(entry["number"], make_pdf=make_pdf)
        results.append(
            {
                "number": entry["number"],
                "docx": str(result["docx"]),
                "pdf": str(result["pdf"]) if result["pdf"] else None,
                "pdf_note": result.get("pdf_note"),
            }
        )
    return {
        "count": len(results),
        "index": index,
        "results": results,
    }
