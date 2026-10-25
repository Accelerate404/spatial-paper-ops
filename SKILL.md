---
name: spatial-paper-ops
description: Engineering discipline for manuscripts built on multi-objective spatial optimization (NSGA-II or similar). Covers figure/table consistency, numeric reconciliation against a single source of truth, submission gates, terminology locking, and post-refactor verification. Use when revising or submitting a paper whose results come from an optimization experiment (land use, regional allocation, spatial planning, zoning constraints), when every number must be traceable to a data source, when a manuscript and its translation disagree, or when you need to prevent "fix one place, break three" consistency failures.
---

# Spatial Paper Ops

This is not a writing tutorial. It is a **criteria handbook**.

Everything here was reverse-engineered from a real geography paper after three months of revision: every incident became an executable criterion. The core proposition is one sentence:

> **If a machine can decide it, never decide it by impression.**

## 1. When to use / when not

**Use it** when a manuscript has left the exploratory stage and entered repeated revision: results are already produced, and numbers, figures, terminology are starting to diverge between files; you are preparing a pre-submission integrity check; you are about to refactor analysis code that produces published results.

**Do not use it** for topic selection, novelty framing, literature synthesis, or language polishing. Delegate those to writing, literature-review, or translation skills.

## 2. Four axioms

1. **Single source of truth.** Each fact has exactly one authoritative origin (numbers → audit workbook, figures → figure directory, terminology → glossary, definitions → project charter). Everything else is derived, and derived artefacts must never modify the origin.
2. **Criteria over impressions.** "Looks fine" is not evidence. Produce an assertion, a file diff, or a count.
3. **Close the loop in one batch.** Change one number, and in the same batch handle every downstream consumer: caption, abstract, supplementary, translated manuscript. Deferring half of it guarantees an omission.
4. **Claims never exceed evidence.** Hedging words must match the actual certainty of the design; repeated hedging cannot substitute for a gap in evidence.

## 3. Six-layer workflow and acceptance criteria

| Layer | Single entry point | Acceptance criterion |
|---|---|---|
| L1 Data | Audit workbook (multi-sheet, sole numeric source) | Every number resolves to `sheet + row/column`; no hand arithmetic, no copying from console logs |
| L2 Experiment | One main-chain script (`run_main.py` or equivalent) | Hard assertions on headline results at the end; seeds fixed; serial and parallel runs agree bit-for-bit |
| L3 Figures | One save function (`_figio._savefig` or equivalent) | Figure count equals declared count; size/type/colour owned by one constants table; per-figure manifest comparison |
| L4 Text | Language-of-record manuscript (everything else derived) | No bold in body text, no colons in headings, three-line tables; zero terminology conflicts with the glossary |
| L5 Reconciliation | Multiset counting script | Numbers, figure IDs, table IDs, reference count agree across sides — **decimal tokens only** |
| L6 Gate | One `gate.py --strict` style command | Exit code is the verdict; re-run after any code change; ship only on PASS |

## 4. Diagnosis order (do not skip steps)

Locate the layer first, then act. A symptom that looks like a figure problem usually originates one layer up.

```
Symptom (a figure or sentence looks wrong)
  → L3 Figures: was the producer overwritten by a retired writer? Was the style entry point skipped?
    → L1 Data: did the workbook change definition while the figure still reads the old sheet?
      → L2 Experiment: is a cached pickle stale? Did the rolling warm-start origin drift?
        → L4 Text: do captions or body still quote the previous definition?
```

Two recurring misdiagnoses: "the figure got ugly" is usually an L1 definition change; "the text is over the word limit" is usually L4 content volume, not translation bloat.

## 5. Twelve hard criteria

1. **No hand arithmetic.** The order is always: run code → verify workbook → edit manuscript. Reversing it means manufacturing your own data.
2. **Three checks on any definition change**: ① residual scan (ranges often omit `%`, producing false negatives) ② line-by-line diff against a frozen snapshot ③ string literals inside the generator source. All three, or the change is not closed.
3. **Integers are not reconciliation evidence.** Figure and table IDs, duplicated bilingual captions, and spelled-out small numbers (`nine cities`) inject three kinds of noise. **Only decimal tokens are evidence.**
4. **One set of numbers cannot serve two comparisons.** Single-objective↔bi-objective and one-shot↔rolling re-optimization are different contrasts; swapping them is fabrication.
5. **Register the sign convention.** The same ablation delta may be written as `full − none` in one table and `none − full` in another. Confirm which convention before cross-referencing. IDs get reused; table headers do not.
6. **When the replacement string contains the original, the criterion is `count(OLD) == count(NEW)`**, not `== 0`.
7. **Line endings: `.gitattributes` is the authority.** Run `git check-attr eol <path>` before editing and verify `git ls-files --eol` afterwards. Do not rely on a verbal convention such as "all markdown is LF". For CRLF files, convert `\n` → `\r\n` before writing multi-line replacements.
8. **Never `git add -A`.** Quarantine directories and deletion staging get swept into the commit. Add explicit paths only; review the full `git status` before committing.
9. **Every figure must call the style entry point itself.** Skipping it silently drops `bbox='tight'`, so the figure is saved at the declared canvas size and the left edge gets clipped. Evidence is the manifest's `bbox_mode`, not "the figure looks empty".
10. **Colour by role, not by figure.** Zones → fixed palette; magnitude → sequential cmap; signed values → diverging cmap; callouts → one accent. Text colour is always computed from the background (`ink_on(bg)`), never hard-coded white.
11. **Compare PNG pixels after a figure change, not PDF checksums.** Verify the per-figure manifest rect counts against a recorded baseline.
12. **Consolidate documentation on a schedule.** Three or more dated files on one topic get merged verbatim into a history directory, originals moved to quarantine, and references re-pointed in a single pass. Otherwise nobody knows which copy is authoritative six months later.

## 6. Three writing disciplines (details in `references/03-writing-discipline.md`)

- **Three prohibitions**: claims never exceed evidence; a paragraph must be globally coherent, not merely locally; hedging must not repeatedly undercut the core conclusion.
- **Three line rules**: colons only for introducing equations, enumerations, and caption field labels (never in headings); no "downward-pointing" structural statements (`this section will…`); no sentence-final defensive disclaimers (substantive limits must survive).
- **No orphan sentences**: inside a paragraph, any non-initial sentence of ≤15 CJK characters is prohibited. The only remedy is merging it into the preceding sentence, and any sentence split must be re-checked against the threshold in the same batch.

## 7. Executable gates (`assets/`)

**A criterion written in prose can still be skipped by a model; a criterion compiled into a script cannot.**

Two layers, deliberately separated — **generic engine, declared anchors**:

- **Engine** (`assets/*.py`): standard library only, zero dependencies, cross-platform, contains no assumptions about any specific project.
- **Configuration** (`gate.toml` in the project): figure count, pixel width, dpi, line endings, truth pairs. **Switching projects means switching the config file, not editing the scripts.**

| Script | What it checks | Ledger refs |
|---|---|---|
| `gate.py` | **Orchestrator**: reads TOML, aggregates results, unifies exit codes; refuses to run on unknown config keys | — |
| `recon_numeric.py` | Decimal-token multiset; figure/table ID **sets**; `$` pairing; registered unit-conversion exceptions | C1 C3 C4 |
| `check_figures.py` | Figure-count guard, naming, pixel width, dpi, write residue (0-byte placeholders), duplicate producers (parses PNG headers) | B1 B7 B8 |
| `check_text.py` | Line endings, heading colons, `$` pairing, curly quotes, inline bold, orphan-sentence candidates | A1 D3 D6 |
| `safe_replace.py` | Replacement-count assertions, bidirectional verification, line-ending preservation, automatic snapshot, dry-run | A3 D1 D2 |

```bash
PY=python
A=path/to/spatial-paper-ops/assets
cp $A/gate.example.toml ./gate.toml     # set the anchors once, then run a single command daily

$PY $A/gate.py                 # all groups
$PY $A/gate.py --list          # show what will run (with waiver annotations)
$PY $A/gate.py --only figures  # one group

# Each script also runs standalone
$PY $A/recon_numeric.py manuscript_zh.md manuscript_en.md --exceptions "1449.8=14.498"
$PY $A/check_figures.py output/figures --expect 7 --width 2244 --code-dir code
$PY $A/check_text.py manuscript.md --strict
$PY $A/safe_replace.py manuscript.md --old "Fig15" --new "Fig03" --expect 4 --dry-run
```

**Three disciplines the scripts themselves obey:**

1. Always print "N items checked"; a mismatch with the expected total is a failure. A regex that silently matches nothing must not pass.
2. Never skip silently. Any `if len(x) == n` guard becomes an assertion or an explicit error. **An unknown key in the config exits with code 2 and refuses to run** — one misspelled `expect` disables one check, which is more dangerous than having no gate at all.
3. Verdicts are binary: hard failure or advisory. Advisory items are for human judgement — **never relax a threshold to manufacture a green light**.

**Waivers, the correct form of flexibility.** For a known issue you do not intend to fix now, register a waiver instead of loosening a threshold:

```toml
[[waiver]]
target = "figures"                  # recon / figures / text
reason = "preview handle left 0-byte placeholders; cleanup pending"
until  = "2026-11-01"               # required; expires back to failure automatically
```

A missing `reason` or `until` is a config error and nothing runs. While a waiver is active, **the raw output is still printed in full** and you are asked to confirm the failing item is still the registered one — new problems must not ride along on an old waiver.

**Exit codes**: `0` pass (possibly with waivers), `1` check failed, `2` configuration error. The third must never be conflated with the second: a config error means the gate never actually ran.

**Known advisory false positives** (expected; do not patch the scripts): orphan-sentence candidates in mixed Chinese/English paragraphs, inline bold in supplementary captions, and genuine emphasis in body text.

## 8. Reference index

| File | What it resolves |
|---|---|
| `references/01-data-and-reproducibility.md` | Single truth channel, definition changes, cache invalidation, assertion gates, the reproducibility triad |
| `references/02-figure-standards.md` | Dimensions, type sizes, single save point, role-based colour, map compliance, routing, pixel comparison |
| `references/03-writing-discipline.md` | Three prohibitions, three line rules, orphan threshold, section transitions, terminology locking |
| `references/04-reconciliation-and-gates.md` | Multiset reconciliation, five word-count definitions, reference closure, submission package boundaries |
| `references/05-pitfall-ledger.md` | 31 real incidents → symptom → root cause → criterion. **Skim before touching anything** |

## 9. Bootstrapping a new project (30-minute checklist)

```
project/
├── AGENTS.md          # the discipline charter (single source; do not duplicate it in README)
├── code/   core/ models/ viz/ cli/     four-layer package; cli holds exactly one main chain
├── data/   audit.xlsx (multi-sheet)    # non-regenerable sources only
├── output/ figures/ (body figures at the root only) / derived/ (regenerable, gitignored)
├── refs/   literature + template.docx (pandoc three-line-table template)
├── workspace/  collaboration-notes.md / glossary.md / history/
└── discuss/    supervisor drafts, meeting minutes (originals)
```

1. Write the collaboration-notes file first, with six empty sections: environment and line endings / data discipline / figures / writing / terminology / git.
2. Then the charter: **definitions and hard constraints only**, no duplicated details. Document scopes must be mutually exclusive.
3. Move every path constant into `core/config.py`; no string literals in business code.
4. The first main-chain script must end with hard assertions on headline results, with expected values read from the workbook, never hard-coded.
5. Reuse `assets/` for gates: run the generic scripts first, then write **that project's** anchors (figure count, column width, line-ending convention) into its own `gate.toml`. Anchors belong to the project; criteria belong to the engine.
6. `data/README.md`: one sentence per sheet describing its definition. **Two sheets with the same name but different definitions must be labelled side by side.**

## 10. Delivery tone

- Lead with the conclusion and its evidence; do not narrate the process.
- When several approaches exist, present options (A/B/C with costs) rather than a single "integrated recommendation".
- Volunteer risks, including "I am not certain about this one; it needs your visual judgement".
- **Never claim to have looked at a figure** if image input is unavailable. Figures get metadata and quantitative verification only (dimensions, dpi, crop, provenance of in-figure numbers); appearance is the user's call.
