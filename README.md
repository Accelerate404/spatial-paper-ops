# spatial-paper-ops

**Engineering discipline for manuscripts built on multi-objective spatial optimization.**

A skill for AI agents (Claude Code, WorkBuddy, and compatible runtimes) that turns the hard-won lessons of a real geography paper into executable criteria — so that "the number in the abstract no longer matches the figure" stops happening.

---

## Why this exists

Papers whose core is an optimization experiment (NSGA-II, zoning constraints, rolling multi-period allocation) accumulate a specific class of defect that no spell-checker finds:

- The abstract quotes a value that the main chain no longer produces.
- One figure was silently overwritten by a retired producer function.
- A definition changed in chapter 2, and six captions still reflect the old one.
- The translated manuscript and the original diverge by 15 decimal values, and nobody knows which side is right.

All of these share one property: **they are machine-decidable, yet they are being decided by impression.** This skill converts them into criteria, and the criteria into scripts whose exit codes cannot be argued with.

## What you get

- **`SKILL.md`** — six-layer workflow, diagnosis order, twelve hard criteria, delivery conventions.
- **`references/`** — five deep-dive documents, including a **31-entry pitfall ledger** (symptom → root cause → criterion). Skim it before touching a manuscript; it is worth a day of debugging.
- **`assets/`** — five dependency-free Python scripts plus a declarative config template.

| Script | Purpose |
|---|---|
| `gate.py` | Orchestrator: reads `gate.toml`, runs groups, aggregates verdicts |
| `recon_numeric.py` | Multiset reconciliation between two manuscripts (decimal tokens, ID sets, math delimiters) |
| `check_figures.py` | Figure-count guard, naming, pixel width, dpi, write residue, duplicate producers |
| `check_text.py` | Line endings, heading colons, `$` pairing, curly quotes, inline bold, orphan sentences |
| `safe_replace.py` | Assertion-guarded find/replace with line-ending preservation and auto-snapshot |

## Install

**As an agent skill** — copy the directory into your skills folder:

```bash
git clone https://github.com/Accelerate404/spatial-paper-ops spatial-paper-ops
cp -r spatial-paper-ops ~/.workbuddy/skills/       # WorkBuddy
# or ~/.claude/skills/ for Claude Code
```

The agent picks it up automatically from `SKILL.md`'s frontmatter.

**As standalone tooling** — the scripts have no agent dependency at all. Copy `assets/` anywhere and run them directly.

## Quick start

```bash
PY=python
A=path/to/spatial-paper-ops/assets

cp $A/gate.example.toml ./gate.toml    # edit the anchors for your project
$PY $A/gate.py --list                  # inspect what will run
$PY $A/gate.py                         # run everything
```

A minimal `gate.toml`:

```toml
[defaults.figures]
fig_dir = "output/figures"
expect  = 7
width   = 2244
dpi     = 300

[defaults.text]
md_eol = "lf"
py_eol = "crlf"

[[recon]]
name  = "manuscript vs translation"
left  = "manuscript_zh.md"
right = "manuscript_en.md"

[[figures]]
code_dir = "code"

[[text]]
paths  = ["manuscript_zh.md"]
strict = true
```

Run the demo on synthetic data instead of your own files:

```bash
$PY tests/run_demo.py
```

## Design principles

1. **Single source of truth.** Every fact has one authoritative origin; everything else is derived and never writes back.
2. **Criteria over impressions.** No "looks fine" — an assertion, a diff, or a count.
3. **Generic engine, declared anchors.** Change projects by changing `gate.toml`. If you have to edit a script for a new paper, the criteria have already begun to fork.
4. **Failures must be loud.** Unknown config keys exit with code 2. Waivers require a reason and an expiry date. Nothing degrades silently.

Exit codes: `0` pass (possibly with waivers) · `1` check failed · `2` configuration error.

## Requirements

- Python **3.9+** for the standalone scripts (standard library only).
- Python **3.11+** for `gate.py` (uses `tomllib`).
- Windows, macOS, Linux. No network access, no third-party packages.

## Repository layout

```
spatial-paper-ops/
├── SKILL.md                     skill entry point (agent-facing)
├── README.md
├── LICENSE
├── CHANGELOG.md
├── references/
│   ├── 01-data-and-reproducibility.md
│   ├── 02-figure-standards.md
│   ├── 03-writing-discipline.md
│   ├── 04-reconciliation-and-gates.md
│   └── 05-pitfall-ledger.md
├── assets/
│   ├── gate.py
│   ├── gate.example.toml
│   ├── recon_numeric.py
│   ├── check_figures.py
│   ├── check_text.py
│   └── safe_replace.py
└── tests/
    ├── run_demo.py              synthetic end-to-end demo
    └── test_gates.py            self-tests for exit-code semantics
```

## Scope and limitations

- The criteria assume a **single-language-of-record** workflow where other language versions are derived. Papers written natively in two languages need the reconciliation thresholds adjusted.
- `check_text.py`'s orphan-sentence rule is calibrated for Chinese prose (15-character threshold). For English-only manuscripts, disable that rule or replace the threshold.
- Map-compliance rules assume Chinese administrative basemaps (standard map service, approval numbers). Other jurisdictions have their own mandated sources — replace that section, do not delete it.
- Figure dimensions default to a 190 mm full-width, 300 dpi Elsevier-style layout. Adjust in `gate.toml`.

## Contributing

Issues and pull requests are welcome, especially **new entries for the pitfall ledger**. An entry is worth adding when it has all three parts:

1. a symptom someone could observe,
2. a root cause that is not obvious from the symptom,
3. a criterion that can be checked mechanically or verified unambiguously by a human.

Please run `python tests/test_gates.py` before submitting.

## License

MIT — see [LICENSE](LICENSE).
