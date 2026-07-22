from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .library import CATEGORIES, PRIMARY_CATEGORIES, normalize_number, save_document_payload


def build_ai_prompt(
    number: str,
    *,
    title: str | None = None,
    category: str | None = None,
    brief: str | None = None,
) -> str:
    """
    Phase 6: prompt for ChatGPT / Claude to return SADS JSON — not a Word file.
    """
    number = normalize_number(number)
    title_line = title or "(propose a clear official title)"
    category_line = category or f"one of: {', '.join(PRIMARY_CATEGORIES)}"
    brief_block = brief.strip() if brief else (
        "Write a practical Spotlight Advocate business document. "
        "Tone: clear, professional, concise. Avoid legalese theater."
    )

    return f"""You are drafting a source document for the Spotlight Advocate Documentation System (SADS).

Do NOT produce a Word file. Do NOT produce Markdown prose alone.
Return ONE JSON object only (no markdown fences, no commentary).

Document number: {number}
Title: {title_line}
Category: {category_line}

Brief:
{brief_block}

Required JSON shape:
{{
  "number": "{number}",
  "title": "...",
  "version": "1.0",
  "category": "Legal",
  "owner": "Spotlight Advocate",
  "approved": "Pending",
  "purpose": "One or two sentences.",
  "scope": "Who/what this applies to.",
  "sections": [
    {{"heading": "Definitions", "type": "definition", "body": "..."}},
    {{"heading": "Procedure", "type": "procedure", "body": "..."}}
  ],
  "revision_history": [
    {{
      "version": "1.0",
      "date": "YYYY-MM-DD",
      "author": "Spotlight Advocate",
      "notes": "Initial draft."
    }}
  ]
}}

Rules:
- category must be exactly one of: {", ".join(PRIMARY_CATEGORIES)}
- Prefer standard section order when relevant: Purpose, Scope, Definitions, Responsibilities, Procedure, Exceptions, References
- Section type should be one of: section, definition, responsibilities, procedure, warning, note, tip, signature, approval, appendix
- Reuse boilerplate with {{{{clause:liability}}}}, {{{{clause:confidentiality}}}}, or {{{{clause:signature-block}}}}
- Include 3–7 focused sections
- Body text should be ready to publish
- Use today's date in revision_history
- Number must sit in the category band (Legal SA-100–199, Operations SA-200–299, Sales SA-300–399, Marketing SA-400–499, HR SA-500–599, Technical SA-600–699, Finance SA-700–799, Administration SA-800–899)
"""


_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)


def parse_ai_json(text: str) -> dict[str, Any]:
    """Extract a JSON object from raw model output (fences allowed)."""
    raw = text.strip()
    if not raw:
        raise ValueError("Empty AI output")

    match = _FENCE_RE.search(raw)
    if match:
        raw = match.group(1).strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Try outermost object
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("Could not find JSON object in AI output")
        data = json.loads(raw[start : end + 1])

    if not isinstance(data, dict):
        raise ValueError("AI output must be a JSON object")
    return data


def import_ai_document(
    source: str | Path,
    *,
    force: bool = False,
) -> Path:
    """
    Import ChatGPT/Claude JSON into Documents/<Category>/SA-xxx.json.

    `source` may be a file path or a raw JSON string.
    """
    if isinstance(source, Path):
        text = source.read_text(encoding="utf-8")
    else:
        text = str(source)
        # Only treat short, path-like strings as files (avoid OSError on huge JSON).
        looks_like_path = (
            "\n" not in text
            and len(text) < 512
            and not text.lstrip().startswith("{")
            and not text.lstrip().startswith("`")
        )
        if looks_like_path:
            path_candidate = Path(text)
            if path_candidate.exists() and path_candidate.is_file():
                text = path_candidate.read_text(encoding="utf-8")

    data = parse_ai_json(text)
    if "number" not in data:
        raise ValueError("Imported JSON is missing number")
    return save_document_payload(data, force=force)
