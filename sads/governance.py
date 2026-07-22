from __future__ import annotations

"""
Publishing rules for SADS (James Tobin recommendations).

Layout is frozen. Content is structured. Numbers and categories are governed.
"""

from typing import Any

from .components import (
    BODY_COMPONENT_TYPES,
    STANDARD_SECTION_ORDER,
    TEMPLATE_COMPONENTS,
    component_catalog,
    section_order_warnings_for_document,
)

# Recommendation 5 + 7 — semantic categories with reserved number bands
CATEGORY_RANGES: dict[str, tuple[int, int]] = {
    "Legal": (100, 199),
    "Operations": (200, 299),
    "Sales": (300, 399),
    "Marketing": (400, 499),
    "HR": (500, 599),
    "Technical": (600, 699),
    "Finance": (700, 799),
    "Administration": (800, 899),
    # Existing library folders kept for compatibility (map into nearby bands)
    "Corporate": (800, 899),  # treat as Administration family
    "Production": (200, 299),  # treat as Operations family
    "Licensing": (100, 199),  # treat as Legal family
}

CATEGORIES = tuple(CATEGORY_RANGES.keys())

PRIMARY_CATEGORIES = (
    "Legal",
    "Operations",
    "Sales",
    "Marketing",
    "HR",
    "Technical",
    "Finance",
    "Administration",
)

# Recommendation 2 — body building blocks (see components.py)
SECTION_TYPES = BODY_COMPONENT_TYPES

# Recommendation 4 — locked metadata fields (authors may not invent others in schema)
METADATA_FIELDS = (
    "number",
    "title",
    "version",
    "category",
    "owner",
    "approved",
)


def number_to_int(number: str) -> int:
    return int(number.strip().upper().split("-", 1)[1])


def expected_range_for_category(category: str) -> tuple[int, int]:
    if category not in CATEGORY_RANGES:
        raise ValueError(
            f"Unknown category {category!r}. Choose one of: {', '.join(PRIMARY_CATEGORIES)}"
        )
    return CATEGORY_RANGES[category]


def category_for_number(number: str) -> str | None:
    """Best-effort primary category guess from SA number band."""
    n = number_to_int(number)
    for cat in PRIMARY_CATEGORIES:
        lo, hi = CATEGORY_RANGES[cat]
        if lo <= n <= hi:
            return cat
    return None


def validate_number_category(number: str, category: str) -> list[str]:
    errors: list[str] = []
    try:
        lo, hi = expected_range_for_category(category)
    except ValueError as exc:
        return [str(exc)]
    try:
        n = number_to_int(number)
    except (IndexError, ValueError):
        return [f"Invalid document number {number!r}"]
    if not (lo <= n <= hi):
        errors.append(
            f"{number} is outside the {category} range SA-{lo:03d}–SA-{hi:03d}"
        )
    return errors


def suggest_next_number(category: str, existing_numbers: list[str]) -> str:
    lo, hi = expected_range_for_category(category)
    used = set()
    for num in existing_numbers:
        try:
            used.add(number_to_int(num))
        except (IndexError, ValueError):
            continue
    for n in range(lo, hi + 1):
        if n not in used:
            return f"SA-{n:03d}"
    raise ValueError(f"No free numbers left in {category} range SA-{lo:03d}–SA-{hi:03d}")


def section_order_warnings(headings: list[str]) -> list[str]:
    """Soft warnings when known standard headings appear out of preferred order."""
    known = [h for h in headings if h.strip() in STANDARD_SECTION_ORDER]
    if len(known) < 2:
        return []
    rank = {name: i for i, name in enumerate(STANDARD_SECTION_ORDER)}
    last = -1
    for h in known:
        r = rank[h.strip()]
        if r < last:
            return [
                "Standard section headings are out of preferred order "
                f"({', '.join(STANDARD_SECTION_ORDER)})."
            ]
        last = r
    return []


def governance_summary() -> dict[str, Any]:
    catalog = component_catalog()
    return {
        "layout_frozen": True,
        "primary_categories": list(PRIMARY_CATEGORIES),
        "category_ranges": {
            cat: {"from": f"SA-{lo:03d}", "to": f"SA-{hi:03d}"}
            for cat, (lo, hi) in CATEGORY_RANGES.items()
            if cat in PRIMARY_CATEGORIES
        },
        "standard_section_order": list(STANDARD_SECTION_ORDER),
        "section_types": list(SECTION_TYPES),
        "metadata_fields": list(METADATA_FIELDS),
        "components": catalog,
        "template_components": list(TEMPLATE_COMPONENTS),
    }


# Re-export for callers that validate whole documents
__all__ = [
    "CATEGORY_RANGES",
    "CATEGORIES",
    "PRIMARY_CATEGORIES",
    "STANDARD_SECTION_ORDER",
    "SECTION_TYPES",
    "METADATA_FIELDS",
    "number_to_int",
    "expected_range_for_category",
    "category_for_number",
    "validate_number_category",
    "suggest_next_number",
    "section_order_warnings",
    "section_order_warnings_for_document",
    "governance_summary",
]
