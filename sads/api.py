from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .ai import build_ai_prompt
from .generate import generate, pdf_backends_available
from .library import (
    CATEGORIES,
    list_documents,
    new_document,
    save_document_payload,
    show_document,
    update_metadata,
    validate_library,
)
from .paths import ROOT, output_docx_dir, output_pdf_dir, template_path
from .portal import build_manual, document_corpus_entry, search_manual
from .rebuild import rebuild_index, rebuild_library
from .template import validate_template


app = FastAPI(
    title="Spotlight Advocate Documentation System",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class NewDocumentBody(BaseModel):
    number: str
    title: str
    category: str
    purpose: str = ""
    scope: str = ""
    owner: Optional[str] = None
    approved: str = "Pending"
    version: str = "1.0"
    force: bool = False


class MetaBody(BaseModel):
    title: Optional[str] = None
    version: Optional[str] = None
    category: Optional[str] = None
    owner: Optional[str] = None
    approved: Optional[str] = None
    notes: Optional[str] = None


class SectionBody(BaseModel):
    heading: str
    body: str


class RevisionBody(BaseModel):
    version: str
    date: str
    author: str
    notes: str


class DocumentPayload(BaseModel):
    number: str
    title: str
    version: str = "1.0"
    category: str
    owner: str = "Spotlight Advocate"
    approved: str = "Pending"
    purpose: str = ""
    scope: str = ""
    sections: list[SectionBody] = Field(default_factory=list)
    revision_history: list[RevisionBody] = Field(default_factory=list)
    force: bool = True


class GenerateBody(BaseModel):
    make_pdf: bool = False


class PromptBody(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    brief: Optional[str] = None


def _http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, FileNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, FileExistsError):
        return HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=400, detail=str(exc))
    return HTTPException(status_code=500, detail=str(exc))


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "project": "SADS"}


@app.get("/api/status")
def status() -> dict[str, Any]:
    tmpl = None
    tmpl_error = None
    try:
        tmpl = str(template_path())
    except FileNotFoundError as exc:
        tmpl_error = str(exc)

    docs = list_documents()
    return {
        "template": tmpl,
        "template_error": tmpl_error,
        "documents": docs,
        "document_count": len(docs),
        "pdf_backends": pdf_backends_available(),
        "categories": list(CATEGORIES),
        "root": str(ROOT),
    }


@app.get("/api/documents")
def documents(category: Optional[str] = None) -> dict[str, Any]:
    docs = list_documents()
    if category:
        docs = [d for d in docs if d["category"] == category]
    return {"documents": docs, "count": len(docs)}


@app.get("/api/manual")
def manual(category: Optional[str] = None) -> dict[str, Any]:
    """Full corpus for the searchable operations manual / portal."""
    return build_manual(category=category)


@app.get("/api/search")
def search(q: str = "", category: Optional[str] = None) -> dict[str, Any]:
    return search_manual(q, category=category)


@app.get("/api/portal/{number}")
def portal_document(number: str) -> dict[str, Any]:
    """Readable web version of one document (not the editor)."""
    try:
        return document_corpus_entry(number)
    except Exception as exc:
        raise _http_error(exc) from exc


@app.get("/api/documents/{number}/summary")
def document_summary(number: str) -> dict[str, Any]:
    try:
        entry = document_corpus_entry(number)
    except Exception as exc:
        raise _http_error(exc) from exc
    return {"number": entry["number"], "title": entry["title"], "summary": entry["summary"]}


@app.get("/api/documents/{number}")
def get_document(number: str) -> dict[str, Any]:
    try:
        info = show_document(number)
    except Exception as exc:
        raise _http_error(exc) from exc
    info["path"] = str(info["path"].relative_to(ROOT))
    return info


@app.post("/api/documents")
def create_document(body: NewDocumentBody) -> dict[str, Any]:
    try:
        path = new_document(
            body.number,
            title=body.title,
            category=body.category,
            purpose=body.purpose,
            scope=body.scope,
            owner=body.owner,
            approved=body.approved,
            version=body.version,
            force=body.force,
        )
    except Exception as exc:
        raise _http_error(exc) from exc
    return {"path": str(path.relative_to(ROOT)), "document": show_document(body.number)}


@app.put("/api/documents/{number}")
def put_document(number: str, body: DocumentPayload) -> dict[str, Any]:
    payload = body.model_dump()
    force = payload.pop("force", True)
    payload["number"] = number.strip().upper()
    try:
        path = save_document_payload(payload, force=force)
    except Exception as exc:
        raise _http_error(exc) from exc
    info = show_document(number)
    info["path"] = str(path.relative_to(ROOT))
    return info


@app.patch("/api/documents/{number}/meta")
def patch_meta(number: str, body: MetaBody) -> dict[str, Any]:
    try:
        path = update_metadata(
            number,
            title=body.title,
            version=body.version,
            category=body.category,
            owner=body.owner,
            approved=body.approved,
            notes=body.notes,
        )
    except Exception as exc:
        raise _http_error(exc) from exc
    info = show_document(number)
    info["path"] = str(path.relative_to(ROOT))
    return info


@app.post("/api/documents/{number}/generate")
def generate_document(number: str, body: Optional[GenerateBody] = None) -> dict[str, Any]:
    make_pdf = body.make_pdf if body else False
    try:
        result = generate(number, make_pdf=make_pdf)
    except Exception as exc:
        raise _http_error(exc) from exc
    return {
        "number": result["number"],
        "docx": str(result["docx"].relative_to(ROOT)) if result["docx"] else None,
        "pdf": str(result["pdf"].relative_to(ROOT)) if result["pdf"] else None,
        "pdf_note": result.get("pdf_note"),
        "download_docx": f"/api/files/docx/{result['number']}",
        "download_pdf": f"/api/files/pdf/{result['number']}" if result["pdf"] else None,
    }


@app.post("/api/rebuild")
def rebuild(body: Optional[GenerateBody] = None) -> dict[str, Any]:
    make_pdf = body.make_pdf if body else False
    try:
        payload = rebuild_library(make_pdf=make_pdf, validate_first=True)
    except Exception as exc:
        raise _http_error(exc) from exc
    results = []
    for item in payload["results"]:
        results.append(
            {
                **item,
                "download_docx": f"/api/files/docx/{item['number']}",
            }
        )
    return {"count": payload["count"], "results": results}


@app.post("/api/index")
def refresh_index() -> dict[str, Any]:
    return rebuild_index()


@app.get("/api/validate")
def validate() -> dict[str, Any]:
    report = validate_library()
    docs = []
    for item in report["documents"]:
        docs.append(
            {
                "number": item["number"],
                "ok": item["ok"],
                "errors": item["errors"],
                "path": str(item["path"].relative_to(ROOT)),
            }
        )
    return {"ok": report["ok"], "count": report["count"], "documents": docs}


@app.get("/api/validate-template")
def validate_tmpl() -> dict[str, Any]:
    try:
        result = validate_template()
    except Exception as exc:
        raise _http_error(exc) from exc
    return {
        "path": str(result["path"].relative_to(ROOT)),
        "ok": result["ok"],
        "missing": result["missing"],
        "is_dotx": result["is_dotx"],
    }


@app.post("/api/prompt/{number}")
def prompt(number: str, body: Optional[PromptBody] = None) -> dict[str, str]:
    body = body or PromptBody()
    text = build_ai_prompt(
        number,
        title=body.title,
        category=body.category,
        brief=body.brief,
    )
    return {"prompt": text}


@app.get("/api/files/{number}/available")
def files_available(number: str) -> dict[str, Any]:
    num = number.strip().upper()
    docx = output_docx_dir() / f"{num}.docx"
    pdf = output_pdf_dir() / f"{num}.pdf"
    return {
        "number": num,
        "docx": docx.exists(),
        "pdf": pdf.exists(),
        "download_docx": f"/api/files/docx/{num}" if docx.exists() else None,
        "download_pdf": f"/api/files/pdf/{num}" if pdf.exists() else None,
    }


@app.get("/api/files/docx/{number}")
def download_docx(number: str):
    path = output_docx_dir() / f"{number.strip().upper()}.docx"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"DOCX not found for {number}")
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=path.name,
    )


@app.get("/api/files/pdf/{number}")
def download_pdf(number: str):
    path = output_pdf_dir() / f"{number.strip().upper()}.pdf"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"PDF not found for {number}")
    return FileResponse(path, media_type="application/pdf", filename=path.name)


# ---------------------------------------------------------------------------
# Production: serve the built React UI from the same FastAPI process
# (one host on Render — build web/dist, then uvicorn sads.api:app)
# ---------------------------------------------------------------------------
_WEB_DIST = ROOT / "web" / "dist"


def _attach_spa() -> None:
    if not _WEB_DIST.exists():
        return

    assets_dir = _WEB_DIST / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/")
    def spa_index():
        return FileResponse(_WEB_DIST / "index.html")

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str):
        # Never steal API routes (safety if ordering ever changes)
        if full_path == "api" or full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        candidate = (_WEB_DIST / full_path).resolve()
        try:
            candidate.relative_to(_WEB_DIST.resolve())
        except ValueError:
            raise HTTPException(status_code=404, detail="Not found") from None
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_WEB_DIST / "index.html")


_attach_spa()
