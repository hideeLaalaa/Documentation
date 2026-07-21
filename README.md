# Spotlight Advocate Documentation System (SADS)

Build the machine that builds documents. Content lives as structured JSON. Formatting lives once in a master Word template. Generation is one command.

## Layout

```
Documentation/
├── Template/                 # Gold master (.dotx / .docx)
├── Documents/                # JSON source of truth by category
│   ├── Corporate/
│   ├── Legal/
│   ├── Operations/
│   ├── Sales/
│   ├── Production/
│   ├── HR/
│   └── Licensing/
├── Output/
│   ├── DOCX/
│   ├── PDF/
│   ├── Archive/
│   └── Images/
├── index.json                # Master index
├── config.json
└── sads/                     # Generator
```

## Setup

```bash
cd "/Users/user/Documents/Spotlight Advocate/Documentation"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m sads.cli init-template
```

That also creates a `.dotx` gold master via Python (no Word Save As required).

Convert an existing `.docx` anytime:

```bash
python3 -m sads.cli to-dotx
# or: python3 -m sads.cli to-dotx Template/SpotlightAdvocate.docx
```

## Commands

```bash
# Generate / rebuild
python3 -m sads.cli generate SA-100
python3 -m sads.cli generate SA-100 --no-pdf
python3 -m sads.cli rebuild

# Library
python3 -m sads.cli new SA-101 --category Legal --title "Document Title"
python3 -m sads.cli list
python3 -m sads.cli show SA-100
python3 -m sads.cli validate
python3 -m sads.cli index
python3 -m sads.cli status

# Metadata (Phase 5)
python3 -m sads.cli meta SA-100 --approved Approved --notes "Signed off."

# AI workflow (Phase 6)
python3 -m sads.cli prompt SA-102 --category Legal --title "..." --brief "..."
python3 -m sads.cli import path/to/ai-output.json --generate --no-pdf

# Template
python3 -m sads.cli validate-template
python3 -m sads.cli to-dotx
python3 -m sads.cli init-template --force
```

## Document source format

Each document is JSON, for example `Documents/Legal/SA-100.json`:

```json
{
  "number": "SA-100",
  "title": "Business Location & Production Release",
  "version": "1.0",
  "category": "Legal",
  "owner": "Spotlight Advocate",
  "approved": "Pending",
  "purpose": "...",
  "scope": "...",
  "sections": [
    { "heading": "Grant of Access", "body": "..." }
  ],
  "revision_history": [
    {
      "version": "1.0",
      "date": "2026-07-21",
      "author": "Spotlight Advocate",
      "notes": "Initial draft."
    }
  ]
}
```

## Workflow

1. Create / edit content as JSON under `Documents/` (or `prompt` → AI → `import`).
2. Set metadata with `meta` / track everything in `index.json`.
3. Edit look-and-feel **only** in `Template/SpotlightAdvocate.dotx`.
4. `generate` one doc, or `rebuild` the whole library.
5. Ship from `Output/DOCX` and `Output/PDF`. Version sources with Git.

For PDF without a paid Word license, install free LibreOffice (`brew install --cask libreoffice`).

Previous outputs are copied into `Output/Archive` before overwrite.
