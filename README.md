# Spotlight Advocate Documentation System (SADS)

Build the machine that builds documents. Content lives as structured JSON. Formatting lives once in a master Word template. Generation is one command — from the CLI or the web UI.

## Web UI (recommended)

Two terminals:

```bash
# Terminal 1 — API
cd "/Users/user/Documents/Spotlight Advocate/Documentation"
source .venv/bin/activate
python3 -m sads.cli serve
```

```bash
# Terminal 2 — frontend
cd "/Users/user/Documents/Spotlight Advocate/Documentation/web"
npm install
npm run dev
```

Open **http://127.0.0.1:5173**

### One-process mode (API serves the UI)

Build the frontend once, then only run the backend — good for **Render**:

```bash
cd "/Users/user/Documents/Spotlight Advocate/Documentation"
source .venv/bin/activate
cd web && npm install && npm run build && cd ..
python3 -m sads.cli serve
```

Then open **http://127.0.0.1:8765** (UI + API on the same port).

### Deploy on Render (single service)

1. Push this `Documentation/` repo (or monorepo root that contains it).
2. Create a **Web Service** → Docker (uses `Dockerfile` + `render.yaml`).
3. Health check: `/api/health`
4. Attach a **persistent disk** mounted at the app root (or at least `Documents/`, `Template/`, `Output/`) so JSON and generated files survive redeploys.

Without a disk, Render’s filesystem is ephemeral — fine for demos, not for a real document library.

PDF on Render needs LibreOffice in the image (optional lines in the Dockerfile).

| Page | What you do |
|------|-------------|
| **Library** | Browse / search / filter · edit sources · rebuild all |
| **Manual** | Searchable operations manual / handbook / licensing views |
| **Portal read** | Web reading view of one document (`/portal/SA-100`) |
| **Document** | Edit title, purpose, scope, sections, metadata · Generate Word |
| **New document** | Create a new SA-xxx JSON source |
| **System** | Template + PDF status · Validate library |

### Same source, many formats

| Output | How |
|--------|-----|
| Word (`.docx`) | Library → open doc → **Generate Word** |
| PDF | Same, when LibreOffice/Word is available |
| Web reading view | **Manual** or **Read** on a library row |
| Searchable manual | **Manual** page (Operations / HR / Licensing filters) |
| AI-style summary | Built into portal “At a glance” (extractive from JSON) |
| Employee handbook / licensing manual | Manual filters by **HR** / **Licensing** categories |

Mental model: **JSON = words**, **template = look**, **Generate / Portal / Manual = formats**.

```bash
cd "/Users/user/Documents/Spotlight Advocate/Documentation"
source .venv/bin/activate
python3 -m sads.cli generate SA-100 --no-pdf
```

---

## Layout

```
Documentation/
├── Template/                 # Gold master (.dotx / .docx)
├── Documents/                # JSON source of truth by category
│   ├── schema.json
│   ├── _template.json
│   ├── Corporate/ Legal/ Operations/ Sales/ Production/ HR/ Licensing/
├── Output/
│   ├── DOCX/                 # Generated Word files
│   ├── PDF/                  # Generated PDFs (if converter available)
│   ├── Archive/              # Previous outputs before overwrite
│   └── Images/
├── index.json                # Master index (metadata registry)
├── config.json               # Paths, placeholders, PDF settings
└── sads/                     # Python package (CLI + generator)
```

---

## Setup

```bash
cd "/Users/user/Documents/Spotlight Advocate/Documentation"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m sads.cli status
```

Optional PDF (no paid Word needed):

```bash
brew install --cask libreoffice
```

---

## Features

### 1. Gold master template (Phase 2)

| Feature | Command | What it does |
|---------|---------|--------------|
| Create template | `init-template` | Builds `SpotlightAdvocate.docx` + `.dotx` |
| Force rebuild template | `init-template --force` | Overwrites both template files |
| Convert to `.dotx` | `to-dotx` | Turns `.docx` into gold master without Word Save As |
| Validate placeholders | `validate-template` | Confirms required `{{PLACEHOLDERS}}` exist |

**Rule:** Edit formatting only in `Template/SpotlightAdvocate.dotx` (or the `.docx` twin, then `to-dotx`). Never hand-edit `Output/`.

Required placeholders:

```
{{NUMBER}} {{TITLE}} {{DOCUMENT_INFO}} {{PURPOSE}} {{SCOPE}}
{{BODY}} {{REVISION_HISTORY}} {{VERSION}}
```

Also supported in mapping: `{{CATEGORY}}` `{{OWNER}}` `{{APPROVED}}`

---

### 2. JSON document database (Phase 3)

| Feature | Command | What it does |
|---------|---------|--------------|
| Create document | `new SA-xxx --category … --title …` | Scaffolds JSON under `Documents/<Category>/` |
| List library | `list` | Shows number, category, version, title, status |
| Validate sources | `validate` | Checks schema/rules for every `SA-*.json` |
| Refresh index | `index` | Rebuilds `index.json` from disk |

Categories: `Corporate` `Legal` `Operations` `Sales` `Production` `HR` `Licensing`

Each source file includes: number, title, version, category, owner, approved, purpose, scope, sections[], revision_history[].

See `Documents/schema.json` and `Documents/_template.json`.

---

### 3. Document generator (Phase 4)

| Feature | Command | What it does |
|---------|---------|--------------|
| Generate one | `generate SA-100` | Template → placeholders → DOCX (+ PDF if available) |
| Skip PDF | `generate SA-100 --no-pdf` | DOCX only |
| Archive on overwrite | *(automatic)* | Copies prior DOCX/PDF into `Output/Archive/` |

Pipeline:

```
Open .dotx → replace placeholders → expand BODY + revisions
→ save Output/DOCX → optional PDF → done
```

---

### 4. Metadata (Phase 5)

| Feature | Command | What it does |
|---------|---------|--------------|
| Show one doc | `show SA-100` | Metadata, purpose/scope, sections, revisions |
| Update metadata | `meta SA-100 --approved Approved` | Writes JSON + refreshes index |
| Version bump | `meta SA-100 --version 1.1 --notes "…"` | Updates version and appends revision history |
| Move category | `meta SA-100 --category Operations` | Moves file to matching folder |

Metadata fields: `--title` `--version` `--category` `--owner` `--approved` `--notes`

---

### 5. AI draft workflow (Phase 6)

| Feature | Command | What it does |
|---------|---------|--------------|
| Print AI brief | `prompt SA-103 --category Legal --title "…" --brief "…"` | Prompt that asks the model for SADS JSON only |
| Import AI JSON | `import path/to/file.json` | Validates and writes into `Documents/` |
| Import + generate | `import file.json --generate --no-pdf` | Import then immediately build DOCX |
| Import from stdin | `import -` | Paste JSON via pipe/stdin |
| Overwrite | `import file.json --force` | Replace an existing number |

AI must return JSON — not a Word file.

---

### 6. Version control (Phase 7)

| Feature | Notes |
|---------|--------|
| Git repo | Initialized in `Documentation/` |
| Tracked | JSON sources, template (`.dotx`/`.docx`), `sads/`, config, index |
| Ignored | `.venv/`, generated `Output/DOCX/*.docx`, `Output/PDF/*.pdf`, `Output/Archive/*` |
| Local archive | Every regenerate also snapshots prior files under `Output/Archive/` |

---

### 7. One-click rebuild (Phase 8)

| Feature | Command | What it does |
|---------|---------|--------------|
| Rebuild library | `rebuild` | Validates all docs, refreshes index, regenerates every DOCX/PDF |
| Rebuild without PDF | `rebuild --no-pdf` | DOCX only |
| Skip validation gate | `rebuild --no-validate` | Rebuild even if a source fails validation |

Change the template once → `rebuild` → every document updates.

---

### 8. System status

| Feature | Command | What it does |
|---------|---------|--------------|
| Status | `status` | Active template, document list, PDF backends |

---

## Commands cheat sheet

```bash
source .venv/bin/activate

# Template
python3 -m sads.cli init-template --force
python3 -m sads.cli to-dotx
python3 -m sads.cli validate-template

# Library
python3 -m sads.cli new SA-200 --category Sales --title "Client Intake Checklist" \
  --purpose "Standardize intake." --scope "All new clients."
python3 -m sads.cli list
python3 -m sads.cli show SA-100
python3 -m sads.cli validate
python3 -m sads.cli index

# Metadata
python3 -m sads.cli meta SA-100 --approved Approved --notes "Signed off."

# AI
python3 -m sads.cli prompt SA-103 --category Legal --title "NDA" --brief "One-page mutual NDA."
python3 -m sads.cli import ~/Downloads/SA-103.json --generate --no-pdf

# Generate / rebuild
python3 -m sads.cli generate SA-100 --no-pdf
python3 -m sads.cli rebuild --no-pdf

# Health
python3 -m sads.cli status
```

---

## Document source format

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

---

## Workflow

1. Create / edit JSON under `Documents/` (or `prompt` → AI → `import`).
2. Set metadata with `meta`; registry lives in `index.json`.
3. Edit look-and-feel only in `Template/SpotlightAdvocate.dotx`.
4. `generate` one doc, or `rebuild` the whole library.
5. Ship from `Output/DOCX` and `Output/PDF`. Commit JSON + template in Git.

---

## How to test all features

Run from the Documentation folder with the venv active:

```bash
cd "/Users/user/Documents/Spotlight Advocate/Documentation"
source .venv/bin/activate
```

Use `--no-pdf` unless LibreOffice (or licensed Word) is installed.

### A. Health & template

| # | Test | Command | Pass if |
|---|------|---------|---------|
| A1 | Status | `python3 -m sads.cli status` | Shows template path + document list |
| A2 | Validate template | `python3 -m sads.cli validate-template` | `Status: OK` |
| A3 | Convert `.docx` → `.dotx` | `python3 -m sads.cli to-dotx` | Prints `Created gold master: …SpotlightAdvocate.dotx` |
| A4 | Rebuild template (optional) | `python3 -m sads.cli init-template --force` | Creates both `.docx` and `.dotx` |

After A4, re-run A2.

### B. Library & validation

| # | Test | Command | Pass if |
|---|------|---------|---------|
| B1 | List | `python3 -m sads.cli list` | Lists SA-100 / SA-101 / SA-102 (or your set) |
| B2 | Show | `python3 -m sads.cli show SA-100` | Prints metadata, sections, revisions |
| B3 | Validate | `python3 -m sads.cli validate` | `All documents OK` |
| B4 | Index | `python3 -m sads.cli index` | Updates `index.json`; count matches `list` |
| B5 | New doc | `python3 -m sads.cli new SA-900 --category HR --title "Test Doc" --purpose "Test." --scope "Test only."` | Creates `Documents/HR/SA-900.json` |
| B6 | Duplicate guard | Re-run B5 without `--force` | Errors with “already exists” |

### C. Metadata

| # | Test | Command | Pass if |
|---|------|---------|---------|
| C1 | Approve | `python3 -m sads.cli meta SA-900 --approved Draft --notes "Test meta."` | `Updated metadata` |
| C2 | Show change | `python3 -m sads.cli show SA-900` | `Approved: Draft`; revision note present |
| C3 | Version bump | `python3 -m sads.cli meta SA-900 --version 1.1 --notes "Bump."` | Version `1.1` + new revision row |
| C4 | Index sync | `python3 -m sads.cli list` | SA-900 shows `v1.1` and `Draft` |

### D. Generator

| # | Test | Command | Pass if |
|---|------|---------|---------|
| D1 | Generate | `python3 -m sads.cli generate SA-100 --no-pdf` | Writes `Output/DOCX/SA-100.docx` |
| D2 | Placeholders gone | Open DOCX (or inspect) | No leftover `{{NUMBER}}` / `{{BODY}}` etc. |
| D3 | Archive | Generate SA-100 again | New file in `Output/Archive/SA-100-*.docx` |
| D4 | PDF (optional) | `python3 -m sads.cli generate SA-100` | Creates `Output/PDF/SA-100.pdf` **or** clear “No PDF converter” message |

### E. AI prompt & import

| # | Test | Command | Pass if |
|---|------|---------|---------|
| E1 | Prompt | `python3 -m sads.cli prompt SA-901 --category Legal --title "Test Release" --brief "Two short sections."` | Prints a JSON-only brief mentioning SA-901 |
| E2 | Import sample | Save the JSON below as `/tmp/SA-901.json`, then `python3 -m sads.cli import /tmp/SA-901.json --force` | Creates `Documents/Legal/SA-901.json` |
| E3 | Import + generate | `python3 -m sads.cli import /tmp/SA-901.json --force --generate --no-pdf` | DOCX at `Output/DOCX/SA-901.docx` |
| E4 | Stdin import | `python3 -m sads.cli import - --force < /tmp/SA-901.json` | Same import success |

Sample `/tmp/SA-901.json`:

```json
{
  "number": "SA-901",
  "title": "Test Release",
  "version": "1.0",
  "category": "Legal",
  "owner": "Spotlight Advocate",
  "approved": "Pending",
  "purpose": "Temporary test document for SADS import.",
  "scope": "Testing only.",
  "sections": [
    { "heading": "Consent", "body": "This is a test section." },
    { "heading": "Use", "body": "Delete after testing." }
  ],
  "revision_history": [
    {
      "version": "1.0",
      "date": "2026-07-21",
      "author": "Spotlight Advocate",
      "notes": "Test import."
    }
  ]
}
```

### F. Rebuild (Phase 8)

| # | Test | Command | Pass if |
|---|------|---------|---------|
| F1 | Rebuild all | `python3 -m sads.cli rebuild --no-pdf` | Regenerates every listed document |
| F2 | Validation gate | Break a JSON field on purpose, run `rebuild --no-pdf` | Aborts with validation errors |
| F3 | Skip gate | `python3 -m sads.cli rebuild --no-pdf --no-validate` | Rebuilds even with a bad file (fix the file after) |

### G. Cleanup after testing

Remove throwaway test docs so the library stays clean:

```bash
rm -f Documents/HR/SA-900.json Documents/Legal/SA-901.json
rm -f Output/DOCX/SA-900.docx Output/DOCX/SA-901.docx
python3 -m sads.cli index
python3 -m sads.cli validate
python3 -m sads.cli list
```

### H. One-shot smoke script

Copy/paste to exercise the core path quickly:

```bash
cd "/Users/user/Documents/Spotlight Advocate/Documentation"
source .venv/bin/activate

python3 -m sads.cli status
python3 -m sads.cli validate-template
python3 -m sads.cli validate
python3 -m sads.cli list
python3 -m sads.cli show SA-100
python3 -m sads.cli generate SA-100 --no-pdf
python3 -m sads.cli rebuild --no-pdf
python3 -m sads.cli prompt SA-902 --category Operations --title "Smoke Test" --brief "One section only." >/dev/null
echo "Smoke OK"
```

---

## PDF notes

- Preferred free path: LibreOffice (`brew install --cask libreoffice`)
- If Word.app is present but unlicensed, PDF export may fail; use `--no-pdf` or LibreOffice
- Check availability anytime with `python3 -m sads.cli status`
