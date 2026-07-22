from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


from .brand import public_brand


@dataclass
class Section:
    heading: str
    body: str
    type: str = "section"
    rows: list[list[str]] | None = None
    src: str = ""
    alt: str = ""


@dataclass
class Revision:
    version: str
    date: str
    author: str
    notes: str  # Description (Recommendation 6)


@dataclass
class Document:
    number: str
    title: str
    version: str
    category: str
    owner: str
    approved: str
    purpose: str = ""
    scope: str = ""
    sections: list[Section] = field(default_factory=list)
    revision_history: list[Revision] = field(default_factory=list)
    source_path: Path | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any], source_path: Path | None = None) -> Document:
        sections = [
            Section(
                heading=s.get("heading", ""),
                body=s.get("body", ""),
                type=(s.get("type") or "section").strip().lower() or "section",
                rows=s.get("rows") if isinstance(s.get("rows"), list) else None,
                src=str(s.get("src") or ""),
                alt=str(s.get("alt") or ""),
            )
            for s in data.get("sections", [])
        ]
        revisions = [
            Revision(
                version=r.get("version", ""),
                date=r.get("date", ""),
                author=r.get("author", ""),
                notes=r.get("notes") or r.get("description", ""),
            )
            for r in data.get("revision_history", [])
        ]
        return cls(
            number=data["number"],
            title=data["title"],
            version=data.get("version", "1.0"),
            category=data.get("category", ""),
            owner=data.get("owner") or public_brand(),
            approved=data.get("approved", "Pending"),
            purpose=data.get("purpose", ""),
            scope=data.get("scope", ""),
            sections=sections,
            revision_history=revisions,
            source_path=source_path,
        )

    def to_index_entry(self) -> dict[str, Any]:
        rel = ""
        if self.source_path is not None:
            try:
                from .paths import ROOT

                rel = str(self.source_path.relative_to(ROOT)).replace("\\", "/")
            except ValueError:
                rel = str(self.source_path)
        return {
            "number": self.number,
            "title": self.title,
            "version": self.version,
            "category": self.category,
            "path": rel,
            "owner": self.owner,
            "approved": self.approved,
        }


def load_document(path: Path) -> Document:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return Document.from_dict(data, source_path=path)


def find_document_file(number: str, documents_root: Path) -> Path:
    needle = number.strip().upper()
    matches = sorted(documents_root.rglob(f"{needle}.json"))
    if not matches:
        raise FileNotFoundError(f"No document source found for {needle}")
    if len(matches) > 1:
        raise RuntimeError(
            f"Multiple sources for {needle}: "
            + ", ".join(str(p) for p in matches)
        )
    return matches[0]
