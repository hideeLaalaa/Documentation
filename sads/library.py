from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from .models import load_document
from .paths import ROOT, documents_root, load_config
from .rebuild import discover_documents, rebuild_index
from .governance import (
    CATEGORIES,
    PRIMARY_CATEGORIES,
    SECTION_TYPES,
    validate_number_category,
    suggest_next_number,
)
from .components import (
    ensure_purpose_scope_sections,
    section_order_warnings_for_document,
    table_rows_from_section,
)


METADATA_FIELDS = ("title", "version", "category", "owner", "approved")

NUMBER_RE = re.compile(r"^SA-\d{3,}$", re.IGNORECASE)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def category_dir(category: str) -> Path:
    if category not in CATEGORIES:
        raise ValueError(
            f"Unknown category {category!r}. Choose one of: {', '.join(CATEGORIES)}"
        )
    path = documents_root() / category
    path.mkdir(parents=True, exist_ok=True)
    return path


def normalize_number(number: str) -> str:
    value = number.strip().upper()
    if not NUMBER_RE.match(value):
        raise ValueError(f"Invalid document number {number!r}. Expected SA-100 style.")
    return value


def document_path(number: str, category: str) -> Path:
    return category_dir(category) / f"{normalize_number(number)}.json"


def new_document(
    number: str,
    *,
    title: str,
    category: str,
    purpose: str = "",
    scope: str = "",
    owner: str | None = None,
    approved: str = "Pending",
    version: str = "1.0",
    force: bool = False,
) -> Path:
    """
    Create a Phase 3 JSON source file under Documents/<Category>/.
    """
    number = normalize_number(number)
    if category not in CATEGORIES:
        raise ValueError(
            f"Unknown category {category!r}. Choose one of: {', '.join(PRIMARY_CATEGORIES)}"
        )
    range_errors = validate_number_category(number, category)
    if range_errors:
        raise ValueError("; ".join(range_errors))

    # Refuse duplicates anywhere in the library
    existing = list(documents_root().rglob(f"{number}.json"))
    dest = document_path(number, category)
    if existing and not force:
        raise FileExistsError(
            f"{number} already exists: "
            + ", ".join(str(p.relative_to(ROOT)) for p in existing)
        )
    if dest.exists() and not force:
        raise FileExistsError(f"Refusing to overwrite {dest}")

    cfg = load_config()
    payload: dict[str, Any] = {
        "number": number,
        "title": title.strip() or f"{number} Untitled",
        "version": version,
        "category": category,
        "owner": owner or cfg.get("owner", "Spotlight Advocate"),
        "approved": approved,
        "purpose": purpose,
        "scope": scope,
        "sections": [
            {
                "heading": "Purpose",
                "type": "section",
                "body": purpose or "State the purpose of this document.",
            },
            {
                "heading": "Scope",
                "type": "section",
                "body": scope or "State who or what this document applies to.",
            },
            {
                "heading": "Definitions",
                "type": "definition",
                "body": "Define key terms used in this document.",
            },
            {
                "heading": "Responsibilities",
                "type": "responsibilities",
                "body": "List who is responsible for what.",
            },
            {
                "heading": "Procedure",
                "type": "procedure",
                "body": "Describe the steps to follow.",
            },
            {
                "heading": "Exceptions",
                "type": "section",
                "body": "Note any exceptions to the standard procedure.",
            },
            {
                "heading": "References",
                "type": "section",
                "body": "List related documents or policies.",
            },
        ],
        "revision_history": [
            {
                "version": version,
                "date": date.today().isoformat(),
                "author": owner or cfg.get("owner", "Spotlight Advocate"),
                "notes": "Initial draft.",
            }
        ],
    }

    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")

    rebuild_index()
    return dest


def validate_document_data(
    data: dict[str, Any],
    *,
    source_path: Path | None = None,
) -> list[str]:
    """Return a list of validation problems (empty means OK)."""
    errors: list[str] = []
    required = (
        "number",
        "title",
        "version",
        "category",
        "owner",
        "approved",
        "purpose",
        "scope",
        "sections",
        "revision_history",
    )
    for key in required:
        if key not in data:
            errors.append(f"missing required field: {key}")

    number = data.get("number")
    if isinstance(number, str):
        if not NUMBER_RE.match(number):
            errors.append(f"invalid number format: {number!r}")
        elif number != number.upper():
            errors.append(f"number must be uppercase: {number!r}")
    elif "number" in data:
        errors.append("number must be a string")

    title = data.get("title")
    if "title" in data and (not isinstance(title, str) or not title.strip()):
        errors.append("title must be a non-empty string")

    category = data.get("category")
    if isinstance(category, str):
        if category not in CATEGORIES:
            errors.append(
                f"invalid category {category!r}; "
                f"expected one of {', '.join(PRIMARY_CATEGORIES)}"
            )
        elif source_path is not None:
            expected_parent = documents_root() / category
            try:
                if source_path.parent.resolve() != expected_parent.resolve():
                    errors.append(
                        f"file is in {source_path.parent.name}/ "
                        f"but category is {category!r}"
                    )
            except OSError:
                pass
        if isinstance(number, str) and NUMBER_RE.match(number):
            errors.extend(validate_number_category(number, category))
    elif "category" in data:
        errors.append("category must be a string")

    if source_path is not None and isinstance(number, str):
        if source_path.stem.upper() != number.upper():
            errors.append(
                f"filename {source_path.name} does not match number {number!r}"
            )

    sections = data.get("sections")
    warnings: list[str] = []
    if "sections" in data:
        if not isinstance(sections, list):
            errors.append("sections must be an array")
        else:
            for i, section in enumerate(sections):
                if not isinstance(section, dict):
                    errors.append(f"sections[{i}] must be an object")
                    continue
                if "heading" not in section or "body" not in section:
                    errors.append(f"sections[{i}] needs heading and body")
                stype = (section.get("type") or "section").strip().lower()
                if stype and stype not in SECTION_TYPES:
                    errors.append(
                        f"sections[{i}].type {stype!r} invalid; "
                        f"expected one of {', '.join(SECTION_TYPES)}"
                    )
                if stype == "table":
                    rows = table_rows_from_section(section)
                    if not rows:
                        errors.append(
                            f"sections[{i}] type=table needs rows or a pipe table in body"
                        )
                if stype == "image" and not str(section.get("src") or "").strip():
                    errors.append(f"sections[{i}] type=image needs src")
            warnings.extend(section_order_warnings_for_document(data))

    revisions = data.get("revision_history")
    if "revision_history" in data:
        if not isinstance(revisions, list):
            errors.append("revision_history must be an array")
        else:
            for i, rev in enumerate(revisions):
                if not isinstance(rev, dict):
                    errors.append(f"revision_history[{i}] must be an object")
                    continue
                # Accept notes or description (Recommendation 6)
                if "notes" not in rev and "description" in rev:
                    rev["notes"] = rev["description"]
                for key in ("version", "date", "author", "notes"):
                    if key not in rev:
                        errors.append(f"revision_history[{i}] missing {key}")
                rev_date = rev.get("date")
                if isinstance(rev_date, str) and not DATE_RE.match(rev_date):
                    errors.append(
                        f"revision_history[{i}].date must be YYYY-MM-DD"
                    )

    return errors, warnings


def validate_document(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    errors, warnings = validate_document_data(data, source_path=path)
    return {
        "path": path,
        "number": data.get("number"),
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
    }


def validate_library() -> dict[str, Any]:
    results = []
    for path in discover_documents():
        results.append(validate_document(path))
    ok = all(item["ok"] for item in results)
    return {"ok": ok, "count": len(results), "documents": results}


def list_documents() -> list[dict[str, Any]]:
    entries = []
    for path in discover_documents():
        doc = load_document(path)
        entries.append(doc.to_index_entry())
    entries.sort(key=lambda d: d["number"])
    return entries


def _read_raw(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _write_raw(path: Path, data: dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def show_document(number: str) -> dict[str, Any]:
    """Phase 5: return metadata + content summary for one document."""
    from .models import find_document_file

    number = normalize_number(number)
    path = find_document_file(number, documents_root())
    data = _read_raw(path)
    doc = load_document(path)
    return {
        "path": path,
        "number": doc.number,
        "title": doc.title,
        "version": doc.version,
        "category": doc.category,
        "owner": doc.owner,
        "approved": doc.approved,
        "purpose": doc.purpose,
        "scope": doc.scope,
        "sections": len(doc.sections),
        "section_headings": [s.heading for s in doc.sections],
        "revision_history": [
            {
                "version": r.version,
                "date": r.date,
                "author": r.author,
                "notes": r.notes,
            }
            for r in doc.revision_history
        ],
        "raw": data,
    }


def update_metadata(
    number: str,
    *,
    title: str | None = None,
    version: str | None = None,
    category: str | None = None,
    owner: str | None = None,
    approved: str | None = None,
    notes: str | None = None,
) -> Path:
    """
    Phase 5: update document metadata in the JSON source and refresh index.

    If version changes, append a revision_history entry.
    If category changes, move the file into the matching folder.
    """
    from .models import find_document_file

    number = normalize_number(number)
    path = find_document_file(number, documents_root())
    data = _read_raw(path)

    updates = {
        "title": title,
        "version": version,
        "category": category,
        "owner": owner,
        "approved": approved,
    }
    applied = {k: v for k, v in updates.items() if v is not None}
    if not applied:
        raise ValueError("No metadata fields provided to update")

    if "category" in applied and applied["category"] not in CATEGORIES:
        raise ValueError(
            f"Unknown category {applied['category']!r}. "
            f"Choose one of: {', '.join(CATEGORIES)}"
        )

    old_version = data.get("version")
    data.update(applied)

    if "version" in applied and applied["version"] != old_version:
        history = data.setdefault("revision_history", [])
        history.append(
            {
                "version": applied["version"],
                "date": date.today().isoformat(),
                "author": data.get("owner", "Spotlight Advocate"),
                "notes": notes or f"Metadata update to version {applied['version']}.",
            }
        )
    elif notes:
        history = data.setdefault("revision_history", [])
        history.append(
            {
                "version": data.get("version", "1.0"),
                "date": date.today().isoformat(),
                "author": data.get("owner", "Spotlight Advocate"),
                "notes": notes,
            }
        )

    errors, _warnings = validate_document_data(data, source_path=path)
    # Category move: validate against destination folder after move
    dest = path
    if "category" in applied:
        dest = document_path(number, applied["category"])
        errors, _warnings = validate_document_data(data, source_path=dest)
    if errors:
        raise ValueError("; ".join(errors))

    if dest != path:
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists() and dest.resolve() != path.resolve():
            raise FileExistsError(f"Target already exists: {dest}")
        _write_raw(dest, data)
        if path.resolve() != dest.resolve():
            path.unlink()
        path = dest
    else:
        _write_raw(path, data)

    rebuild_index()
    return path


def save_document_payload(data: dict[str, Any], *, force: bool = False) -> Path:
    """Write a full document JSON payload into the correct category folder."""
    number = normalize_number(str(data.get("number", "")))
    category = data.get("category")
    if category not in CATEGORIES:
        raise ValueError(
            f"Unknown category {category!r}. Choose one of: {', '.join(CATEGORIES)}"
        )
    data = ensure_purpose_scope_sections(dict(data))
    data["number"] = number

    dest = document_path(number, category)
    existing = list(documents_root().rglob(f"{number}.json"))
    if existing and not force:
        # Allow overwrite only of the same path when force is set
        raise FileExistsError(
            f"{number} already exists: "
            + ", ".join(str(p.relative_to(ROOT)) for p in existing)
            + " (use --force to overwrite)"
        )

    errors, _warnings = validate_document_data(data, source_path=dest)
    if errors:
        raise ValueError("; ".join(errors))

    # Remove stale copies in other categories when forcing
    if force:
        for old in existing:
            if old.resolve() != dest.resolve():
                old.unlink()

    dest.parent.mkdir(parents=True, exist_ok=True)
    _write_raw(dest, data)
    rebuild_index()
    return dest
