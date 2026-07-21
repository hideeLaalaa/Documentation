# Phase 3 — Document Database (JSON)

Word files are **outputs**. Content lives here as JSON.

```
Documents/
├── schema.json          # Contract for every document
├── _template.json       # Blank example (not indexed)
├── Corporate/
├── Legal/
│   └── SA-100.json
├── Operations/
├── Sales/
├── Production/
├── HR/
└── Licensing/
```

## Why JSON

- Tiny and easy to edit
- Easy for Git and AI
- Same source can later become Word, PDF, web, handbook, licensing manual

## Create a document

```bash
python3 -m sads.cli new SA-101 \
  --category Legal \
  --title "Your Document Title" \
  --purpose "Why it exists." \
  --scope "Who it covers."
```

Then edit `Documents/<Category>/SA-101.json` and generate:

```bash
python3 -m sads.cli generate SA-101
```

## Metadata

```bash
python3 -m sads.cli show SA-100
python3 -m sads.cli meta SA-100 --approved Approved --notes "Signed off."
```

## AI draft → import

```bash
python3 -m sads.cli prompt SA-102 --category Legal --title "..." --brief "..."
# paste prompt into ChatGPT / Claude, save JSON, then:
python3 -m sads.cli import ~/Downloads/SA-102.json --generate --no-pdf
```

## Validate / list

```bash
python3 -m sads.cli validate
python3 -m sads.cli list
python3 -m sads.cli index
```

## Required shape

See `schema.json` and `_template.json`. Minimum fields:

- `number`, `title`, `version`, `category`, `owner`, `approved`
- `purpose`, `scope`
- `sections[]` with `heading` + `body`
- `revision_history[]` with `version`, `date`, `author`, `notes`

`category` must match the folder name.
