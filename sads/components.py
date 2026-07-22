from __future__ import annotations

"""
Reusable document building blocks (Recommendation 2).

Documents assemble components. Presentation (how a component looks) lives in the
renderer / gold master — not in JSON.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .paths import ROOT, resolve


# Recommendation 8 — preferred section order when present
STANDARD_SECTION_ORDER = (
    "Purpose",
    "Scope",
    "Definitions",
    "Responsibilities",
    "Procedure",
    "Exceptions",
    "References",
    "Revision History",
)


# Shared template-owned blocks (one place for the whole library)
TEMPLATE_COMPONENTS = (
    "header",
    "metadata",
    "footer",
    "revision_table",
)

# Author-assembled body blocks
BODY_COMPONENT_TYPES = (
    "section",
    "paragraph",
    "definition",
    "responsibilities",
    "procedure",
    "warning",
    "note",
    "tip",
    "signature",
    "approval",
    "appendix",
    "table",
    "image",
)

# Alias used across the codebase
SECTION_TYPES = BODY_COMPONENT_TYPES


@dataclass
class Component:
    """Normalized building block ready for a renderer."""

    type: str
    heading: str = ""
    body: str = ""
    rows: list[list[str]] = field(default_factory=list)
    src: str = ""
    alt: str = ""


def component_catalog() -> dict[str, Any]:
    return {
        "template_owned": list(TEMPLATE_COMPONENTS),
        "body_types": list(BODY_COMPONENT_TYPES),
        "notes": {
            "header": "Gold master header (logo + brand)",
            "metadata": "Document Number, Title, Version, Category, Owner, Status",
            "footer": "Gold master footer",
            "revision_table": "{{REVISION_HISTORY}} → Version / Date / Author / Description",
            "paragraph": "Body text without a section heading treatment",
            "table": "Use rows: [[header...],[cell...]] or pipe rows in body",
            "image": "Use src (path under project) + body as caption",
        },
    }


def parse_pipe_table(text: str) -> list[list[str]]:
    """Parse a simple pipe table from body text."""
    rows: list[list[str]] = []
    for line in (text or "").splitlines():
        line = line.strip()
        if not line or set(line) <= {"|", "-", " ", ":"}:
            continue
        if "|" not in line:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells:
            rows.append(cells)
    return rows


def table_rows_from_section(section: dict[str, Any] | Component) -> list[list[str]]:
    if isinstance(section, Component):
        if section.rows:
            return [list(r) for r in section.rows]
        return parse_pipe_table(section.body)
    raw = section.get("rows")
    if isinstance(raw, list) and raw:
        out: list[list[str]] = []
        for row in raw:
            if isinstance(row, list):
                out.append([str(c) for c in row])
            else:
                out.append([str(row)])
        return out
    return parse_pipe_table(str(section.get("body") or ""))


def resolve_image_path(src: str) -> Path | None:
    """Resolve an image path relative to project root or Output/Images."""
    if not src or not str(src).strip():
        return None
    raw = str(src).strip()
    candidates = [
        Path(raw),
        ROOT / raw,
        resolve(raw),
        resolve(f"Output/Images/{Path(raw).name}"),
        resolve(f"Components/Images/{Path(raw).name}"),
    ]
    for path in candidates:
        try:
            if path.is_file():
                return path.resolve()
        except OSError:
            continue
    return None


def component_from_dict(data: dict[str, Any]) -> Component:
    stype = (data.get("type") or "section").strip().lower() or "section"
    return Component(
        type=stype,
        heading=str(data.get("heading") or ""),
        body=str(data.get("body") or ""),
        rows=table_rows_from_section(data) if stype == "table" else [],
        src=str(data.get("src") or ""),
        alt=str(data.get("alt") or data.get("heading") or ""),
    )


def has_heading(sections: list[dict[str, Any]], name: str) -> bool:
    needle = name.strip().lower()
    return any((s.get("heading") or "").strip().lower() == needle for s in sections)


def ensure_purpose_scope_sections(data: dict[str, Any]) -> dict[str, Any]:
    """
    Recommendation 8 — Purpose and Scope lead the body when present as metadata.

    Keeps top-level purpose/scope fields (metadata) and mirrors them as leading
    sections so ordering is consistent in the assembled document.
    """
    data = dict(data)
    sections = [dict(s) for s in (data.get("sections") or [])]
    purpose = (data.get("purpose") or "").strip()
    scope = (data.get("scope") or "").strip()

    lead: list[dict[str, Any]] = []
    if purpose and not has_heading(sections, "Purpose"):
        lead.append({"heading": "Purpose", "type": "section", "body": purpose})
    if scope and not has_heading(sections, "Scope"):
        lead.append({"heading": "Scope", "type": "section", "body": scope})

    # If Purpose/Scope already exist, sync body from metadata when metadata is non-empty
    for section in sections:
        heading = (section.get("heading") or "").strip().lower()
        if heading == "purpose" and purpose:
            section["body"] = purpose
        elif heading == "scope" and scope:
            section["body"] = scope

    data["sections"] = lead + sections
    return data


def assemble_body_components(
    *,
    purpose: str,
    scope: str,
    sections: list[Any],
    include_purpose_scope: bool = True,
) -> list[Component]:
    """
    Build the ordered list of body components for rendering.

    Injects Purpose / Scope from metadata when those headings are absent.
    Set include_purpose_scope=False when the template already renders
    {{PURPOSE}} / {{SCOPE}} above the body (avoids duplication in Word).
    """
    raw_sections: list[dict[str, Any]] = []
    for item in sections:
        if hasattr(item, "heading"):
            raw_sections.append(
                {
                    "heading": item.heading,
                    "body": item.body,
                    "type": getattr(item, "type", "section"),
                    "rows": getattr(item, "rows", None) or [],
                    "src": getattr(item, "src", "") or "",
                    "alt": getattr(item, "alt", "") or "",
                }
            )
        else:
            raw_sections.append(dict(item))

    probe = ensure_purpose_scope_sections(
        {"purpose": purpose, "scope": scope, "sections": raw_sections}
    )
    components = [component_from_dict(s) for s in probe["sections"]]
    if not include_purpose_scope:
        components = [
            c
            for c in components
            if c.heading.strip().lower() not in {"purpose", "scope"}
        ]
    return components


def section_order_warnings_for_document(data: dict[str, Any]) -> list[str]:
    """Order checks against the assembled body (including injected Purpose/Scope)."""
    assembled = assemble_body_components(
        purpose=str(data.get("purpose") or ""),
        scope=str(data.get("scope") or ""),
        sections=list(data.get("sections") or []),
    )
    headings = [c.heading for c in assembled if c.heading]
    warnings: list[str] = []

    known = [h for h in headings if h.strip() in STANDARD_SECTION_ORDER]
    if len(known) >= 2:
        rank = {name: i for i, name in enumerate(STANDARD_SECTION_ORDER)}
        last = -1
        for h in known:
            r = rank[h.strip()]
            if r < last:
                warnings.append(
                    "Standard section headings are out of preferred order "
                    f"({', '.join(STANDARD_SECTION_ORDER)})."
                )
                break
            last = r

    # Soft nudge: operations-style docs benefit from the full spine
    present = {h.strip() for h in known}
    if "Procedure" in present or "Responsibilities" in present:
        missing = [
            name
            for name in ("Definitions", "Responsibilities", "Procedure", "Exceptions", "References")
            if name not in present
        ]
        if missing:
            warnings.append(
                "Consider adding standard sections when applicable: "
                + ", ".join(missing)
            )
    return warnings
