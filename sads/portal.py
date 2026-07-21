from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

from .library import show_document
from .paths import ROOT
from .rebuild import discover_documents


def _haystack(doc: dict[str, Any]) -> str:
    parts = [
        doc.get("number", ""),
        doc.get("title", ""),
        doc.get("category", ""),
        doc.get("purpose", ""),
        doc.get("scope", ""),
        doc.get("owner", ""),
        doc.get("approved", ""),
    ]
    for section in doc.get("sections", []):
        parts.append(section.get("heading", ""))
        parts.append(section.get("body", ""))
    return "\n".join(parts).lower()


def document_corpus_entry(number_or_path: str | Path) -> dict[str, Any]:
    """Full structured document for portal / manual rendering."""
    if isinstance(number_or_path, Path):
        from .models import load_document

        number = load_document(number_or_path).number
    else:
        number = str(number_or_path)

    info = show_document(number)
    raw = info["raw"]
    path = info["path"]
    rel = str(path.relative_to(ROOT)) if isinstance(path, Path) else str(path)
    return {
        "number": raw["number"],
        "title": raw["title"],
        "version": raw["version"],
        "category": raw["category"],
        "owner": raw["owner"],
        "approved": raw["approved"],
        "purpose": raw["purpose"],
        "scope": raw["scope"],
        "sections": raw["sections"],
        "revision_history": raw["revision_history"],
        "path": rel,
        "summary": summarize_document(raw),
    }


def build_manual(category: Optional[str] = None) -> dict[str, Any]:
    """Searchable operations-style manual assembled from all JSON sources."""
    entries = []
    for path in discover_documents():
        entry = document_corpus_entry(path)
        if category and entry["category"] != category:
            continue
        entries.append(entry)
    entries.sort(key=lambda d: (d["category"], d["number"]))
    categories = sorted({e["category"] for e in entries})
    return {
        "title": "Spotlight Advocate Operations Manual",
        "document_count": len(entries),
        "categories": categories,
        "documents": entries,
    }


def search_manual(query: str, category: Optional[str] = None) -> dict[str, Any]:
    q = query.strip().lower()
    manual = build_manual(category=category)
    if not q:
        return {
            "query": query,
            "count": manual["document_count"],
            "results": [
                {
                    "number": d["number"],
                    "title": d["title"],
                    "category": d["category"],
                    "approved": d["approved"],
                    "version": d["version"],
                    "snippet": (d["purpose"] or "")[:180],
                    "matches": [],
                }
                for d in manual["documents"]
            ],
        }

    tokens = [t for t in re.split(r"\s+", q) if t]
    results = []
    for doc in manual["documents"]:
        hay = _haystack(doc)
        if not all(tok in hay for tok in tokens):
            continue
        matches = []
        for field, label in (
            ("title", "Title"),
            ("purpose", "Purpose"),
            ("scope", "Scope"),
        ):
            text = doc.get(field, "") or ""
            if any(tok in text.lower() for tok in tokens):
                matches.append({"field": label, "excerpt": _excerpt(text, tokens)})
        for section in doc.get("sections", []):
            blob = f"{section.get('heading', '')} {section.get('body', '')}"
            if any(tok in blob.lower() for tok in tokens):
                matches.append(
                    {
                        "field": section.get("heading") or "Section",
                        "excerpt": _excerpt(blob, tokens),
                    }
                )
        results.append(
            {
                "number": doc["number"],
                "title": doc["title"],
                "category": doc["category"],
                "approved": doc["approved"],
                "version": doc["version"],
                "snippet": (doc["purpose"] or "")[:180],
                "matches": matches[:6],
            }
        )
    return {"query": query, "count": len(results), "results": results}


def summarize_document(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Lightweight extractive summary from structured source (no external AI).

    Good enough for portal cards; can later swap for an LLM call.
    """
    purpose = (raw.get("purpose") or "").strip()
    scope = (raw.get("scope") or "").strip()
    headings = [s.get("heading", "") for s in raw.get("sections", []) if s.get("heading")]
    bullets = []
    if purpose:
        bullets.append(purpose)
    if scope:
        bullets.append(f"Applies to: {scope}")
    for section in raw.get("sections", [])[:3]:
        body = (section.get("body") or "").strip()
        if not body:
            continue
        first = re.split(r"(?<=[.!?])\s+", body)[0]
        if first:
            bullets.append(f"{section.get('heading', 'Section')}: {first}")
    return {
        "headline": raw.get("title", ""),
        "bullets": bullets[:5],
        "section_count": len(raw.get("sections", [])),
        "topics": headings,
    }


def _excerpt(text: str, tokens: list[str], radius: int = 70) -> str:
    lower = text.lower()
    idx = -1
    hit = ""
    for tok in tokens:
        idx = lower.find(tok)
        if idx >= 0:
            hit = tok
            break
    if idx < 0:
        return text[:140] + ("…" if len(text) > 140 else "")
    start = max(0, idx - radius)
    end = min(len(text), idx + len(hit) + radius)
    chunk = text[start:end].strip()
    if start > 0:
        chunk = "…" + chunk
    if end < len(text):
        chunk = chunk + "…"
    return chunk
