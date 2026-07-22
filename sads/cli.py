#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow `python -m sads.cli` and `python sads/cli.py`
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sads.ai import build_ai_prompt, import_ai_document
from sads.generate import generate, pdf_backends_available
from sads.library import (
    CATEGORIES,
    list_documents,
    new_document,
    show_document,
    update_metadata,
    validate_library,
)
from sads.paths import resolve, template_path
from sads.rebuild import rebuild_index, rebuild_library
from sads.template import build_master_template, docx_to_dotx, validate_template


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sads",
        description="Spotlight Advocate Documentation System",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="Generate one document, e.g. SA-100")
    gen.add_argument("number", help="Document number, e.g. SA-100")
    gen.add_argument("--no-pdf", action="store_true", help="Skip PDF export")

    reb = sub.add_parser("rebuild", help="Rebuild entire library from JSON sources")
    reb.add_argument("--no-pdf", action="store_true", help="Skip PDF export")
    reb.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip validation gate before rebuild",
    )

    sub.add_parser("index", help="Refresh master index.json from Documents/")
    sub.add_parser("list", help="List document sources in the library")

    show = sub.add_parser("show", help="Show metadata and summary for one document")
    show.add_argument("number", help="Document number, e.g. SA-100")

    meta = sub.add_parser("meta", help="Update document metadata (Phase 5)")
    meta.add_argument("number", help="Document number, e.g. SA-100")
    meta.add_argument("--title", default=None)
    meta.add_argument("--version", default=None)
    meta.add_argument("--category", choices=CATEGORIES, default=None)
    meta.add_argument("--owner", default=None)
    meta.add_argument("--approved", default=None, help='e.g. Pending / Approved')
    meta.add_argument("--notes", default=None, help="Revision note to append")

    new = sub.add_parser("new", help="Create a new JSON document source")
    new.add_argument("number", help="Document number, e.g. SA-101")
    new.add_argument("--title", required=True, help="Document title")
    new.add_argument(
        "--category",
        required=True,
        choices=CATEGORIES,
        help="Category folder under Documents/",
    )
    new.add_argument("--purpose", default="", help="Purpose text")
    new.add_argument("--scope", default="", help="Scope text")
    new.add_argument("--owner", default=None, help="Document owner")
    new.add_argument("--approved", default="Pending", help="Approval status")
    new.add_argument("--version", default="1.0", help="Starting version")
    new.add_argument("--force", action="store_true", help="Overwrite if exists")

    prompt = sub.add_parser(
        "prompt",
        help="Print an AI brief that returns SADS JSON (Phase 6)",
    )
    prompt.add_argument("number", help="Document number, e.g. SA-102")
    prompt.add_argument("--title", default=None)
    prompt.add_argument("--category", choices=CATEGORIES, default=None)
    prompt.add_argument("--brief", default=None, help="Extra instructions for the model")

    imp = sub.add_parser(
        "import",
        help="Import AI JSON into Documents/ (Phase 6)",
    )
    imp.add_argument(
        "source",
        help="Path to a .json file, or pass '-' to read JSON from stdin",
    )
    imp.add_argument("--force", action="store_true", help="Overwrite if exists")
    imp.add_argument(
        "--generate",
        action="store_true",
        help="Also generate DOCX after import",
    )
    imp.add_argument("--no-pdf", action="store_true", help="Skip PDF when --generate")

    sub.add_parser("validate", help="Validate all JSON document sources")

    init = sub.add_parser("init-template", help="Create gold-master Word template")
    init.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing template (.docx and .dotx)",
    )

    to_dotx = sub.add_parser(
        "to-dotx",
        help="Convert a .docx to .dotx without Microsoft Word",
    )
    to_dotx.add_argument(
        "source",
        nargs="?",
        default="Template/SpotlightAdvocate.docx",
        help="Source .docx path (default: Template/SpotlightAdvocate.docx)",
    )
    to_dotx.add_argument(
        "-o",
        "--output",
        default=None,
        help="Destination .dotx path (default: same name with .dotx)",
    )

    sub.add_parser(
        "validate-template",
        help="Confirm gold master exists and has required placeholders",
    )
    sub.add_parser(
        "status",
        help="Show system status (template, library, PDF backends)",
    )

    serve = sub.add_parser("serve", help="Start the web UI API server")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)

    args = parser.parse_args(argv)

    if args.command == "generate":
        result = generate(args.number, make_pdf=not args.no_pdf)
        print(f"Generated {result['number']}")
        print(f"  Source:   {result['source']}")
        print(f"  Template: {result['template']}")
        print(f"  DOCX:     {result['docx']}")
        if result["pdf"]:
            print(f"  PDF:      {result['pdf']}")
        else:
            print(f"  PDF:      {result['pdf_note']}")
        return 0

    if args.command == "rebuild":
        try:
            payload = rebuild_library(
                make_pdf=not args.no_pdf,
                validate_first=not args.no_validate,
            )
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print(f"Rebuilt {payload['count']} document(s)")
        for item in payload["results"]:
            print(f"  {item['number']}: {item['docx']}")
            if item["pdf"]:
                print(f"           pdf={item['pdf']}")
            else:
                print(f"           pdf={item.get('pdf_note') or 'n/a'}")
        return 0

    if args.command == "index":
        payload = rebuild_index()
        print(f"Indexed {len(payload['documents'])} document(s) -> {resolve('index.json')}")
        return 0

    if args.command == "list":
        docs = list_documents()
        if not docs:
            print("No documents found under Documents/")
            return 0
        for entry in docs:
            print(
                f"{entry['number']}  [{entry['category']}]  "
                f"v{entry['version']}  {entry['title']}  ({entry['approved']})"
            )
        return 0

    if args.command == "show":
        try:
            info = show_document(args.number)
        except FileNotFoundError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        print(f"{info['number']}  —  {info['title']}")
        print(f"  Version:   {info['version']}")
        print(f"  Category:  {info['category']}")
        print(f"  Owner:     {info['owner']}")
        print(f"  Approved:  {info['approved']}")
        print(f"  Path:      {info['path'].relative_to(ROOT)}")
        print(f"  Purpose:   {info['purpose']}")
        print(f"  Scope:     {info['scope']}")
        print(f"  Sections:  {info['sections']}")
        for heading in info["section_headings"]:
            print(f"    - {heading}")
        print("  Revisions:")
        for rev in info["revision_history"]:
            print(
                f"    - {rev['version']}  {rev['date']}  "
                f"{rev['author']}  —  {rev['notes']}"
            )
        return 0

    if args.command == "meta":
        try:
            path = update_metadata(
                args.number,
                title=args.title,
                version=args.version,
                category=args.category,
                owner=args.owner,
                approved=args.approved,
                notes=args.notes,
            )
        except (ValueError, FileExistsError, FileNotFoundError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        print(f"Updated metadata: {path.relative_to(ROOT)}")
        print("Index refreshed. Run generate/rebuild to refresh Word output.")
        return 0

    if args.command == "new":
        try:
            path = new_document(
                args.number,
                title=args.title,
                category=args.category,
                purpose=args.purpose,
                scope=args.scope,
                owner=args.owner,
                approved=args.approved,
                version=args.version,
                force=args.force,
            )
        except (ValueError, FileExistsError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        print(f"Created {path.relative_to(ROOT)}")
        print("Edit the JSON, then: python3 -m sads.cli generate " + args.number.upper())
        return 0

    if args.command == "prompt":
        text = build_ai_prompt(
            args.number,
            title=args.title,
            category=args.category,
            brief=args.brief,
        )
        print(text)
        return 0

    if args.command == "import":
        source = sys.stdin.read() if args.source == "-" else args.source
        try:
            path = import_ai_document(source, force=args.force)
        except (ValueError, FileExistsError, json.JSONDecodeError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        print(f"Imported {path.relative_to(ROOT)}")
        if args.generate:
            result = generate(path.stem, make_pdf=not args.no_pdf)
            print(f"Generated {result['number']}")
            print(f"  DOCX: {result['docx']}")
            if result["pdf"]:
                print(f"  PDF:  {result['pdf']}")
            else:
                print(f"  PDF:  {result['pdf_note']}")
        return 0

    if args.command == "validate":
        report = validate_library()
        print(f"Validated {report['count']} document(s)")
        failed = 0
        for item in report["documents"]:
            rel = item["path"].relative_to(ROOT)
            if item["ok"]:
                print(f"  OK   {item['number']}  ({rel})")
                for warn in item.get("warnings") or []:
                    print(f"       ! {warn}")
            else:
                failed += 1
                print(f"  FAIL {item['number']}  ({rel})")
                for err in item["errors"]:
                    print(f"       - {err}")
        if failed:
            print(f"{failed} document(s) failed validation")
            return 1
        print("All documents OK")
        return 0

    if args.command == "init-template":
        dest = resolve("Template/SpotlightAdvocate.docx")
        dotx = dest.with_suffix(".dotx")
        if (dest.exists() or dotx.exists()) and not args.force:
            print(f"Template already exists: {dest if dest.exists() else dotx}")
            print("Use --force to overwrite, or run: python3 -m sads.cli to-dotx")
            return 1
        path = build_master_template(dest)
        gold = docx_to_dotx(path, dotx)
        print(f"Created master template: {path}")
        print(f"Created gold master:     {gold}")
        return 0

    if args.command == "to-dotx":
        source = Path(args.source)
        if not source.is_absolute():
            source = resolve(str(source))
        output = Path(args.output) if args.output else None
        if output is not None and not output.is_absolute():
            output = resolve(str(output))
        gold = docx_to_dotx(source, output)
        print(f"Created gold master: {gold}")
        return 0

    if args.command == "validate-template":
        result = validate_template()
        print(f"Gold master: {result['path']}")
        print(f"  Format:  {'.dotx' if result['is_dotx'] else result['path'].suffix}")
        if result["ok"]:
            print("  Status:  OK — all required placeholders present")
            return 0
        print("  Status:  MISSING placeholders:")
        for ph in result["missing"]:
            print(f"    - {ph}")
        return 1

    if args.command == "status":
        tmpl = None
        tmpl_err = None
        try:
            tmpl = template_path()
        except FileNotFoundError as exc:
            tmpl_err = str(exc)

        docs = list_documents()
        backends = pdf_backends_available()
        print("Spotlight Advocate Documentation System")
        if tmpl:
            print(f"  Template: {tmpl}")
        else:
            print(f"  Template: MISSING ({tmpl_err})")
        print(f"  Documents: {len(docs)}")
        for entry in docs:
            print(
                f"    - {entry['number']} [{entry['category']}] "
                f"v{entry['version']} {entry['approved']} — {entry['title']}"
            )
        if backends:
            print("  PDF backends:")
            for name in backends:
                print(f"    - {name}")
        else:
            print("  PDF backends: none")
            print("    Install free LibreOffice for PDF export:")
            print("    brew install --cask libreoffice")
        return 0

    if args.command == "serve":
        import os

        try:
            import uvicorn
        except ImportError:
            print(
                "Error: install API deps with: pip install fastapi 'uvicorn[standard]'",
                file=sys.stderr,
            )
            return 1

        host = args.host
        port = args.port
        # Render (and similar) inject PORT
        if os.environ.get("PORT"):
            port = int(os.environ["PORT"])
            if args.host == "127.0.0.1":
                host = "0.0.0.0"

        dist = ROOT / "web" / "dist"
        print(f"SADS server → http://{host}:{port}")
        if dist.exists():
            print("  UI: served from web/dist (same origin)")
        else:
            print("  UI: not built — run: cd web && npm run build")
            print("       or for local Vite: cd web && npm run dev")
        uvicorn.run(
            "sads.api:app",
            host=host,
            port=port,
            reload=False,
        )
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
