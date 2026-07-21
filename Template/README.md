# Phase 2 — Gold Master Template

**Only file that defines formatting:**

```
Template/SpotlightAdvocate.dotx
```

That is the gold master. Never hand-edit files in `Output/` for look-and-feel. Change the template once; rebuild the library.

Full feature list and test plan: see [`../README.md`](../README.md).

## Files in this folder

| File | Role |
|------|------|
| `SpotlightAdvocate.dotx` | **Gold master** — generator prefers this |
| `SpotlightAdvocate.docx` | Working twin (same content); use if you edit in LibreOffice / Pages, then convert |

## Rules

1. Edit formatting **only** in the gold master (or its `.docx` twin, then convert).
2. Keep these placeholders exactly as written — the generator depends on them:

```
{{NUMBER}}
{{TITLE}}
{{DOCUMENT_INFO}}
{{PURPOSE}}
{{SCOPE}}
{{BODY}}
{{REVISION_HISTORY}}
{{VERSION}}
```

3. Never hand-edit `Output/DOCX` or `Output/PDF`. Those are generated.

## Commands

```bash
# Rebuild polished .docx + .dotx from code
python3 -m sads.cli init-template --force

# Convert an edited .docx → .dotx (no paid Word)
python3 -m sads.cli to-dotx

# Confirm placeholders are intact
python3 -m sads.cli validate-template
```
