from __future__ import annotations

"""
Global brand / legal identity for SADS.

Public brand is what audiences see. Legal company is the contracting entity.
"""

from typing import Any

from docx.shared import RGBColor

from .paths import load_config


# Defaults — config.json brand block overrides these
DEFAULTS: dict[str, str] = {
    "legal_company": "Spotlight Media Holdings LLC",
    "public_brand": "Spotlight Advocate",
    "tagline": "Building Trust Through Real Conversations",
    "website": "spotlightadvocate.com",
    "copyright": "Spotlight Media Holdings LLC",
    "primary_color": "Navy",
    "accent_color": "Antique Gold",
    "primary_hex": "#1A2B4A",
    "accent_hex": "#C5A572",
}


def brand() -> dict[str, str]:
    cfg = load_config().get("brand") or {}
    out = dict(DEFAULTS)
    for key, value in cfg.items():
        if value is not None and str(value).strip():
            out[key] = str(value).strip()
    # Legacy aliases
    if "LEGAL_COMPANY" in cfg:
        out["legal_company"] = str(cfg["LEGAL_COMPANY"]).strip()
    if "PUBLIC_BRAND" in cfg:
        out["public_brand"] = str(cfg["PUBLIC_BRAND"]).strip()
    if "TAGLINE" in cfg:
        out["tagline"] = str(cfg["TAGLINE"]).strip()
    if "WEBSITE" in cfg:
        out["website"] = str(cfg["WEBSITE"]).strip()
    if "COPYRIGHT" in cfg:
        out["copyright"] = str(cfg["COPYRIGHT"]).strip()
    if "PRIMARY_COLOR" in cfg:
        out["primary_color"] = str(cfg["PRIMARY_COLOR"]).strip()
    if "ACCENT_COLOR" in cfg:
        out["accent_color"] = str(cfg["ACCENT_COLOR"]).strip()
    return out


def public_brand() -> str:
    return brand()["public_brand"]


def legal_company() -> str:
    return brand()["legal_company"]


def tagline() -> str:
    return brand()["tagline"]


def website() -> str:
    return brand()["website"]


def copyright_holder() -> str:
    return brand()["copyright"]


def _hex_to_rgb(value: str) -> RGBColor:
    h = value.strip().lstrip("#")
    if len(h) != 6:
        h = "1A2B4A"
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def primary_rgb() -> RGBColor:
    return _hex_to_rgb(brand()["primary_hex"])


def accent_rgb() -> RGBColor:
    return _hex_to_rgb(brand()["accent_hex"])


def brand_placeholders() -> dict[str, str]:
    b = brand()
    return {
        "{{LEGAL_COMPANY}}": b["legal_company"],
        "{{PUBLIC_BRAND}}": b["public_brand"],
        "{{TAGLINE}}": b["tagline"],
        "{{WEBSITE}}": b["website"],
        "{{COPYRIGHT}}": b["copyright"],
        "{{PRIMARY_COLOR}}": b["primary_color"],
        "{{ACCENT_COLOR}}": b["accent_color"],
    }


def brand_summary() -> dict[str, Any]:
    b = brand()
    return {
        "legal_company": b["legal_company"],
        "public_brand": b["public_brand"],
        "tagline": b["tagline"],
        "website": b["website"],
        "copyright": b["copyright"],
        "primary_color": b["primary_color"],
        "accent_color": b["accent_color"],
        "primary_hex": b["primary_hex"],
        "accent_hex": b["accent_hex"],
    }
