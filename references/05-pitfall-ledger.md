# 05 · Pitfall Ledger

Format: **symptom → root cause → criterion**. Skim this before touching anything; it is an order of magnitude cheaper than debugging afterwards.

## A. Files and versions

**A1 · Line endings changed and the mistake was written into the commit message**
Symptom: a file was converted to LF following the verbal convention "all markdown is LF", but it was registered as CRLF.
Root cause: git applies "the last matching rule wins" per file, so exceptions depend on rule order. A verbal convention is not an authority.
Criterion: run `git check-attr eol <path>` before editing, and verify `w/` against `attr/` in `git ls-files --eol` after. **`.gitattributes` is the first authority.**

**A2 · `git add -A` swept quarantine deletions into the commit**
Root cause: quarantine directories sit on the gitignore boundary; `-A` carries the deletion.
Criterion: add explicit paths only; review the full `git status`; verify with `rev-parse HEAD` after committing.

**A3 · A file pushed to a preview panel cannot be overwritten at the same path**
Root cause: the preview holds a long-lived file handle.
Criterion: write to a dated filename or a different path before overwriting. Regenerable artefacts (docx) are the usual victims.

**A4 · A command executed twice**
Symptom: a script using `>>` appended its output twice.
Root cause: some shell shims retry.
Criterion: every write script must be **idempotent + replacing + doubly asserted** (assert the old state is gone and the new state exists).

## B. Figures

**B1 · A final figure silently overwritten**
Symptom: a figure reverted to an older version although nobody edited figure code.
Root cause: a retired producer remained importable and wrote the same filename, or two modules exposed the same function name.
Criterion: a health check treats "duplicate producer for a figure name" as a hard failure; exactly one rendering entry point per body figure.

**B2 · Left edge clipped**
Root cause: the style entry point was skipped, so `savefig.bbox` was not `tight` and the figure was saved without cropping.
Criterion: every manifest entry reports `bbox_mode = tight`. **Not "the figure looks empty".**

**B3 · Colours changed quietly**
Root cause: retired producers still carry two stale palettes; remounting one overwrites the colours.
Criterion: the palette definition file is the single authority; check for a second definition of `ZONE*` / `CMAP_*`.

**B4 · White text on a light background**
Root cause: `color='white'` hard-coded.
Criterion: text colour recognises only the return value of `ink_on(bg)` or a sampled pixel.

**B5 · Figure disagrees with the workbook**
Root cause: a cached pickle was stale; the figure read the old cache.
Criterion: the manifest records the source workbook's mtime or size hash; recompute when the cache is older.

**B6 · A provincial panel cannot be drawn**
Root cause: the EPS standard map uses CorelDRAW page coordinates, the shapefile uses EPSG:3857, and the residual of a forced fit reaches several percent of province width.
Criterion: **if georeferencing cannot reach a residual below 0.5%, do not produce the panel**; express the information differently. Do not treat this as "someone forgot to draw it" and force it back in.

**B7 · The wrong criterion was used to judge a figure change**
Root cause: comparing PDF checksums (vector metadata changes even when pixels do not).
Criterion: compare PNG pixels or per-figure manifest `kept_n` against a recorded baseline.

**B8 · 0-byte placeholder files mixed into the figure directory**
Symptom: hidden files such as `.FigNN_Name.png.k3j9x2.png` or `.FigNN_Name.pdf.bzr7f03k.pdf` appear at the figure root and the count guard reports an overrun.
Root cause: `savefig` had its target handle held (editor preview, sync client, preview panel), so matplotlib left a 0-byte placeholder and failed. The real figure survives, which is why it goes unnoticed.
Criterion: any hidden file whose name contains `.png.` or `.pdf.` is residue and is always 0 bytes. Move it to quarantine; **never count it as a body figure**. If it recurs, find the process holding the handle.

## C. Numbers and reconciliation

**C1 · A reconciliation script passed without checking anything**
Root cause: `if len(rows) == 7:` made the check **skip** when the row count was unexpected; or the entry regex accepted only single parentheses, dropping entries silently.
Criterion: the gate must print "items checked" and compare it to the expected total. **Skipped ≠ passed.**

**C2 · Self-defeating defence**
Symptom: a script contains `raise ValueError('reconciliation mismatch')` that has never fired.
Root cause: the whole block was wrapped in `except Exception`, which swallowed the script's own error.
Criterion: search for `raise` inside `try` blocks; `raise` inside `except` is a defect by definition.

**C3 · Integer-token reconciliation is all noise**
Root cause: IDs, duplicated bilingual captions, spelled-out small numbers.
Criterion: **decimals only** — the observed decimal difference is zero while integers differ by dozens.

**C4 · One set of deltas used for two different contrasts**
Symptom: `2.10%` and `13.06%` were treated as the same quantity, but one belongs to single-objective↔bi-objective and the other to one-shot↔rolling re-optimization.
Root cause: both contrasts involve "efficiency loss", so they look alike.
Criterion: **bind every number group to a unique contrast label**, register the label as the workbook row name, and move the label with the number into the text.

**C5 · Ablation sign convention inverted**
Root cause: the detail table uses `full − without X` and the summary table uses `without X − full`.
Criterion: read the table header before cross-referencing; never rely on remembered IDs (IDs are reused, headers are not).

**C6 · Definition changed but the number printed on the figure is old**
Root cause: the workbook was updated correctly, but the annotation came from an f-string literal in the source.
Criterion: check ③ of the definition-change protocol — generator source literals — cannot be skipped.

**C7 · Assertion expected values hard-coded in the script**
Root cause: convenience — `assert x == 12.6601`.
Criterion: expected values are always read from the workbook. Hard-coding means the code and the manuscript can be wrong together and the assertion still passes.

## D. Text

**D1 · The old string survives the replacement**
Root cause: the replacement contains the original (e.g. `constraint boundary` → `spatial constraint boundary`), so `count(OLD) == 0` can never hold.
Criterion: `count(OLD) == count(NEW)`.

**D2 · Two edits in one file overwrote each other**
Criterion: change one place at a time and assert immediately. Snapshot before large edits.

**D3 · Splitting a sentence produced an orphan**
Root cause: only fluency was checked, not the threshold.
Criterion: any non-initial sentence of ≤15 CJK characters inside a paragraph is an orphan; splitting requires re-checking in the same batch.

**D4 · Renumbering a section left dangling pointers in the supplementary**
Root cause: the gate checked the main manuscript only; the supplementary file was a blind spot.
Criterion: renumbering requires grepping the supplementary file and the citation-support bank for `§` references.

**D5 · A supervisor's annotation was copied as an instruction**
Root cause: a margin note may be a question, or a misunderstanding.
Criterion: verify against the source before rewriting literature; verify the facts before renaming a term. Real case: a supervisor annotated a penalty coefficient as a "temporal boundary coefficient" although it belongs to the constraint-boundary layer, defined in the same equation as another coefficient. Copying it would have been an error.

**D6 · A de-AI tool damaged a final draft**
Root cause: general-purpose suggestions collided with journal prohibitions (curly quotes, sentence splitting, hedging removal).
Criterion: the tool defaults to a problem list only; if rewriting, disable colliding rules first, limit scope, and re-run the gates.

## E. Code refactoring

**E1 · A facade generator wrote broken code and a full run was wasted**
Symptom: the forwarding block landed after the `if __name__ == '__main__'` guard, or a parenthesis was missing, or `join` inserted extra blank lines.
Root cause: the generator itself was never verified before writing.
Criterion: **dry-run the generator and print first.** Verification order: AST structural equivalence → verbatim equivalence → `dir()` set equivalence → artefact checksums. **Not "the figure looks empty".**

**E2 · Refactoring broke a figure in passing**
Criterion: compare checksums of every produced artefact before and after (all 28 PNGs byte-identical), not "I checked two and they looked the same".

**E3 · Defensive code removed too aggressively**
Calibration: delete only **silent degradation** (a panel silently not drawn, reconciliation falling back to the old value, `except: pass` swallowing the script's own error). Do **not** delete four categories: numeric branch fallbacks, fail-fast existence checks (`raise FileNotFoundError('run … first')`), normal control flow (skipping failed initial points in multi-start optimisation), and delayed failures. Converting the last category into an immediate raise only moves the error.

## F. Collaboration

**F1 · Sub-agents fabricate references and numbers**
Criterion: reconcile every number by multiset; verify every reference against its source (at least title, year, journal); grep the actual file to confirm any "already modified" claim.

**F2 · A decision the user already made is silently overturned by a later edit**
Criterion: read the decision log in the collaboration notes before editing. Any change that conflicts with an existing decision is proposed first, executed second.

**F3 · The agent claims to have looked at a figure**
Calibration: without image input, figures get metadata and quantitative verification only; appearance is the user's judgement. **Never describe a figure you have not read.**
