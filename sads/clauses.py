from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .paths import ROOT, resolve


CLAUSE_REF_RE = re.compile(
    r"\{\{\s*(?:clause:([a-z0-9_-]+)|Standard\s+([^}]+?)\s+Clause)\s*\}\}",
    re.IGNORECASE,
)


def clauses_dir() -> Path:
    path = resolve("Components/Clauses")
    path.mkdir(parents=True, exist_ok=True)
    return path


def list_clauses() -> list[dict[str, Any]]:
    items = []
    for path in sorted(clauses_dir().glob("*.json")):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        items.append(
            {
                "id": data.get("id", path.stem),
                "title": data.get("title", path.stem),
                "path": str(path.relative_to(ROOT)),
                "body": data.get("body", ""),
            }
        )
    return items


def load_clause(clause_id: str) -> dict[str, Any]:
    needle = clause_id.strip().lower().replace(" ", "-")
    path = clauses_dir() / f"{needle}.json"
    if not path.exists():
        # try title slug match
        for item in list_clauses():
            if item["id"].lower() == needle or item["title"].lower() == clause_id.strip().lower():
                path = ROOT / item["path"]
                break
        else:
            raise FileNotFoundError(f"Unknown clause: {clause_id}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def expand_clause_references(text: str) -> str:
    """
    Expand reusable boilerplate references in body text.

    Supported forms:
      {{clause:liability}}
      {{ Standard Liability Clause }}
    """

    def repl(match: re.Match[str]) -> str:
        clause_id = match.group(1)
        title_form = match.group(2)
        key = clause_id or (title_form or "").strip().lower().replace(" ", "-")
        # Map common title forms
        key = key.replace("standard-", "").replace("-clause", "")
        aliases = {
            "liability": "liability",
            "confidentiality": "confidentiality",
            "signature-block": "signature-block",
            "signature": "signature-block",
        }
        key = aliases.get(key, key)
        try:
            data = load_clause(key)
        except FileNotFoundError:
            return match.group(0)  # leave unresolved token visible
        return (data.get("body") or "").strip()

    return CLAUSE_REF_RE.sub(repl, text)


def ensure_default_clauses() -> None:
    defaults = [
        {
            "id": "liability",
            "title": "Standard Liability Clause",
            "body": (
                "Except to the extent caused by Spotlight Media Holdings LLC's gross negligence or "
                "willful misconduct, Spotlight Media Holdings LLC's aggregate liability arising out of "
                "or related to this document shall not exceed the fees paid (if any) for the "
                "specific engagement giving rise to the claim."
            ),
        },
        {
            "id": "confidentiality",
            "title": "Standard Confidentiality Clause",
            "body": (
                "Each party shall keep confidential the non-public information of the other "
                "party obtained in connection with this engagement and shall not disclose it "
                "to third parties except as required by law or with prior written consent."
            ),
        },
        {
            "id": "signature-block",
            "title": "Standard Signature Block",
            "body": (
                "IN WITNESS WHEREOF, the parties have executed this document as of the date "
                "first written above.\n\n"
                "Spotlight Media Holdings LLC\n"
                "d/b/a Spotlight Advocate: ___________________________  Date: __________\n\n"
                "Counterparty: ________________________________  Date: __________"
            ),
        },
    ]
    folder = clauses_dir()
    for item in defaults:
        path = folder / f"{item['id']}.json"
        if not path.exists():
            with open(path, "w", encoding="utf-8") as f:
                json.dump(item, f, indent=2)
                f.write("\n")
