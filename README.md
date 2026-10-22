# jp-balance-sheet-parser

Parse Japanese consolidated balance sheets (連結貸借対照表) from PDF into structured CSV and JSON.

> **Status**: Phase 0 — project scaffolding complete. Parsing logic coming in later phases.

## Quick start

```bash
# 1. Clone and enter the repo
git clone <repo-url> && cd jp-balance-sheet-parser

# 2. Create a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -e ".[dev]"

# 4. Run tests
pytest
```

## Repository layout

```
├── src/
│   └── parser/          # Main Python package
│       └── __init__.py
├── tests/               # Pytest test suite
│       └── test_smoke.py
├── data/
│   ├── raw/             # Original PDFs (tracked in git)
│   └── gt/              # Hand-labeled ground-truth files
├── outputs/             # Generated CSV / JSON (git-ignored)
├── eval/                # Evaluation scripts and configs
├── scripts/             # CLI entry points and utilities
├── notes/               # Design notes and scratch work
├── PROJECT_BRIEF.md     # Full task description and plan
└── pyproject.toml       # Python project metadata and deps
```

## Dependencies

| Package | Purpose |
|---|---|
| PyMuPDF | Low-level PDF text + coordinate extraction |
| pdfplumber | Higher-level table / layout extraction |
| pandas | Tabular data manipulation and CSV output |
| pytest | Test runner |
| ruff | Linter / formatter |

## Usage

_To be documented as parsing logic is implemented._

## License

This project is a take-home assignment and is not licensed for redistribution.
