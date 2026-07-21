from __future__ import annotations

import io
import shutil
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path

from docx import Document as WordDocument
from docx.oxml import OxmlElement
from docx.shared import Pt, RGBColor
from docx.text.paragraph import Paragraph

from .models import Document, find_document_file, load_document
from .paths import (
    archive_dir,
    documents_root,
    load_config,
    output_docx_dir,
    output_pdf_dir,
    template_path,
)
from .template import DOCX_MAIN_CONTENT_TYPE, DOTX_MAIN_CONTENT_TYPE

NAVY = RGBColor(0x1A, 0x2B, 0x4A)
GRAY = RGBColor(0x55, 0x55, 0x55)

LIBREOFFICE_CANDIDATES = (
    "soffice",
    "libreoffice",
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    "/usr/local/bin/soffice",
    "/opt/homebrew/bin/soffice",
)


def _open_word_template(path: Path) -> WordDocument:
    """
    Open a .docx or .dotx master template.

    python-docx only accepts document.main content types, so .dotx packages
    are remapped in memory before loading.
    """
    path = Path(path)
    if path.suffix.lower() != ".dotx":
        return WordDocument(str(path))

    buffer = io.BytesIO()
    with zipfile.ZipFile(path, "r") as zin, zipfile.ZipFile(
        buffer, "w", compression=zipfile.ZIP_DEFLATED
    ) as zout:
        for info in zin.infolist():
            data = zin.read(info.filename)
            if info.filename == "[Content_Types].xml":
                text = data.decode("utf-8").replace(
                    DOTX_MAIN_CONTENT_TYPE, DOCX_MAIN_CONTENT_TYPE
                )
                data = text.encode("utf-8")
            zout.writestr(info, data)
    buffer.seek(0)
    return WordDocument(buffer)


def _style_run(
    run,
    *,
    size: int = 11,
    bold: bool = False,
    color: RGBColor | None = None,
    name: str = "Calibri",
) -> None:
    run.bold = bold
    run.font.size = Pt(size)
    run.font.name = name
    if color is not None:
        run.font.color.rgb = color


def _replace_in_paragraph(paragraph, mapping: dict[str, str]) -> None:
    if not paragraph.runs:
        text = paragraph.text
        for key, value in mapping.items():
            text = text.replace(key, value)
        if text != paragraph.text:
            paragraph.text = text
        return

    full = "".join(run.text for run in paragraph.runs)
    updated = full
    for key, value in mapping.items():
        updated = updated.replace(key, value)
    if updated == full:
        return

    paragraph.runs[0].text = updated
    for run in paragraph.runs[1:]:
        run.text = ""


def _clear_paragraph(paragraph: Paragraph) -> None:
    for run in paragraph.runs:
        run.text = ""
    if not paragraph.runs:
        paragraph.text = ""


def _insert_paragraph_after(paragraph: Paragraph) -> Paragraph:
    new_p = OxmlElement("w:p")
    paragraph._p.addnext(new_p)
    return Paragraph(new_p, paragraph._parent)


def _find_placeholder_paragraph(doc: WordDocument, placeholder: str) -> Paragraph | None:
    for paragraph in doc.paragraphs:
        if placeholder in paragraph.text:
            return paragraph
    return None


def _write_paragraph(
    paragraph: Paragraph,
    text: str,
    *,
    size: int = 11,
    bold: bool = False,
    color: RGBColor | None = None,
    space_after: int = 6,
) -> None:
    _clear_paragraph(paragraph)
    run = paragraph.add_run(text)
    _style_run(run, size=size, bold=bold, color=color)
    paragraph.paragraph_format.space_after = Pt(space_after)
    paragraph.paragraph_format.space_before = Pt(0)


def _expand_body_placeholder(doc: WordDocument, document: Document) -> None:
    """Replace {{BODY}} with section headings + body paragraphs."""
    target = _find_placeholder_paragraph(doc, "{{BODY}}")
    if target is None:
        return

    _clear_paragraph(target)
    if not document.sections:
        return

    anchor = target
    first = True
    for section in document.sections:
        if first:
            _write_paragraph(
                anchor,
                section.heading,
                size=13,
                bold=True,
                color=NAVY,
                space_after=4,
            )
            first = False
        else:
            anchor = _insert_paragraph_after(anchor)
            _write_paragraph(
                anchor,
                section.heading,
                size=13,
                bold=True,
                color=NAVY,
                space_after=4,
            )

        body_chunks = [c.strip() for c in section.body.split("\n\n") if c.strip()]
        if not body_chunks:
            body_chunks = [section.body.strip()] if section.body.strip() else [""]

        for chunk in body_chunks:
            anchor = _insert_paragraph_after(anchor)
            _write_paragraph(anchor, chunk, size=11, space_after=8)

        # Breathing room between sections
        anchor = _insert_paragraph_after(anchor)
        _write_paragraph(anchor, "", size=11, space_after=4)


def _expand_revision_placeholder(doc: WordDocument, document: Document) -> None:
    """Replace {{REVISION_HISTORY}} with one line per revision."""
    target = _find_placeholder_paragraph(doc, "{{REVISION_HISTORY}}")
    if target is None:
        return

    _clear_paragraph(target)
    revisions = document.revision_history
    if not revisions:
        _write_paragraph(
            target,
            "No revisions recorded.",
            size=9,
            color=GRAY,
            space_after=4,
        )
        return

    anchor = target
    first = True
    for rev in revisions:
        line = f"{rev.version}  ·  {rev.date}  ·  {rev.author}  ·  {rev.notes}"
        if first:
            _write_paragraph(anchor, line, size=9, color=GRAY, space_after=2)
            first = False
        else:
            anchor = _insert_paragraph_after(anchor)
            _write_paragraph(anchor, line, size=9, color=GRAY, space_after=2)


def _replace_placeholders(doc: WordDocument, mapping: dict[str, str]) -> None:
    for paragraph in doc.paragraphs:
        _replace_in_paragraph(paragraph, mapping)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    _replace_in_paragraph(paragraph, mapping)

    for section in doc.sections:
        for header in (section.header, section.first_page_header, section.even_page_header):
            for paragraph in header.paragraphs:
                _replace_in_paragraph(paragraph, mapping)
        for footer in (section.footer, section.first_page_footer, section.even_page_footer):
            for paragraph in footer.paragraphs:
                _replace_in_paragraph(paragraph, mapping)


def _format_document_info(document: Document) -> str:
    return (
        f"Version {document.version}  ·  Category: {document.category}  ·  "
        f"Owner: {document.owner}  ·  Status: {document.approved}"
    )


def _archive_existing(path: Path) -> None:
    if not path.exists():
        return
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = archive_dir() / f"{path.stem}-{stamp}{path.suffix}"
    archive_dir().mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)


def pdf_backends_available() -> list[str]:
    """Return human-readable names of PDF converters found on this machine."""
    found: list[str] = []
    # Presence of Word.app does not guarantee an activated/licensed install.
    word = Path("/Applications/Microsoft Word.app")
    if word.exists():
        found.append("Microsoft Word.app (may require license)")
    for binary in LIBREOFFICE_CANDIDATES:
        path = Path(binary) if binary.startswith("/") else shutil.which(binary)
        if path and Path(path).exists():
            found.append(f"LibreOffice ({path})")
            break
    return found


def _export_pdf(docx_path: Path, pdf_path: Path) -> tuple[Path | None, str | None]:
    """
    Export DOCX → PDF.

    Returns (pdf_path, None) on success, or (None, reason) when skipped/unavailable.
    """
    cfg = load_config().get("pdf", {})
    if not cfg.get("enabled", True):
        return None, "PDF disabled in config.json"

    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    method = cfg.get("method", "auto")

    # Microsoft Word via AppleScript (works with full Word installs)
    if method in ("auto", "word"):
        word_script = f'''
        tell application "Microsoft Word"
          set theDoc to open POSIX file "{docx_path}"
          save as theDoc file name POSIX file "{pdf_path}" file format format PDF
          close theDoc saving no
        end tell
        '''
        try:
            result = subprocess.run(
                ["osascript", "-e", word_script],
                capture_output=True,
                text=True,
                check=False,
                timeout=120,
            )
            if result.returncode == 0 and pdf_path.exists():
                return pdf_path, None
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    # LibreOffice / soffice (free; preferred when Word is unpaid / unavailable)
    if method in ("auto", "libreoffice"):
        for binary in LIBREOFFICE_CANDIDATES:
            resolved = binary if binary.startswith("/") else shutil.which(binary)
            if not resolved or not Path(resolved).exists():
                continue
            try:
                result = subprocess.run(
                    [
                        str(resolved),
                        "--headless",
                        "--convert-to",
                        "pdf",
                        "--outdir",
                        str(pdf_path.parent),
                        str(docx_path),
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=180,
                )
                produced = pdf_path.parent / f"{docx_path.stem}.pdf"
                if result.returncode == 0 and produced.exists():
                    if produced != pdf_path:
                        produced.replace(pdf_path)
                    return pdf_path, None
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue

    return (
        None,
        "No PDF converter found. Install free LibreOffice, or use --no-pdf. "
        "Then: brew install --cask libreoffice",
    )


def generate(number: str, *, make_pdf: bool = True) -> dict:
    """
    Phase 4 pipeline:

    Open template → replace placeholders → expand body/revisions →
    save DOCX → optional PDF → done.
    """
    number = number.strip().upper()
    source = find_document_file(number, documents_root())
    document = load_document(source)
    template = template_path()

    mapping = {
        "{{NUMBER}}": document.number,
        "{{TITLE}}": document.title,
        "{{PURPOSE}}": document.purpose,
        "{{SCOPE}}": document.scope,
        "{{VERSION}}": document.version,
        "{{CATEGORY}}": document.category,
        "{{OWNER}}": document.owner,
        "{{APPROVED}}": document.approved,
        "{{DOCUMENT_INFO}}": _format_document_info(document),
        # Expanded separately; leave empty if a stray token remains
        "{{REVISION_HISTORY}}": "",
        "{{BODY}}": "",
    }

    out_docx = output_docx_dir() / f"{document.number}.docx"
    out_pdf = output_pdf_dir() / f"{document.number}.pdf"
    output_docx_dir().mkdir(parents=True, exist_ok=True)

    _archive_existing(out_docx)
    if make_pdf:
        _archive_existing(out_pdf)

    word = _open_word_template(template)
    _expand_body_placeholder(word, document)
    _expand_revision_placeholder(word, document)
    _replace_placeholders(word, mapping)
    word.save(str(out_docx))

    pdf_result: Path | None = None
    pdf_note: str | None = None
    if make_pdf:
        pdf_result, pdf_note = _export_pdf(out_docx, out_pdf)
    else:
        pdf_note = "skipped (--no-pdf)"

    return {
        "number": document.number,
        "docx": out_docx,
        "pdf": pdf_result,
        "pdf_note": pdf_note,
        "source": source,
        "template": template,
    }
