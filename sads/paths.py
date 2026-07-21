from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent


def load_config() -> dict[str, Any]:
    with open(ROOT / "config.json", encoding="utf-8") as f:
        return json.load(f)


def resolve(relative: str) -> Path:
    return ROOT / relative


def documents_root() -> Path:
    return resolve(load_config()["paths"]["documents"])


def output_docx_dir() -> Path:
    return resolve(load_config()["paths"]["output_docx"])


def output_pdf_dir() -> Path:
    return resolve(load_config()["paths"]["output_pdf"])


def archive_dir() -> Path:
    return resolve(load_config()["paths"]["archive"])


def index_path() -> Path:
    return resolve(load_config()["paths"]["index"])


def template_path() -> Path:
    cfg = load_config()["paths"]
    primary = resolve(cfg["template"])
    if primary.exists():
        return primary
    fallback = resolve(cfg["template_fallback"])
    if fallback.exists():
        return fallback
    raise FileNotFoundError(
        "No master template found. Place SpotlightAdvocate.dotx "
        f"(or .docx) in {resolve('Template')}."
    )
